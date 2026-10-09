from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction

from .models import Category, Product, Order, OrderItem, Wishlist

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from decimal import Decimal


def home(request):

    featured_products = Product.objects.filter(
        is_active=True,
        is_featured=True
    )[:6]

    return render(
        request,
        "store/home.html",
        {
            "featured_products": featured_products
        }
    )


def shop(request):

    products = Product.objects.filter(
        is_active=True
    )

    categories = Category.objects.all()

    search = request.GET.get(
        "search",
        ""
    )

    category = request.GET.get(
        "category",
        ""
    )

    if search:
        products = products.filter(
            name__icontains=search
        )

    if category:
        products = products.filter(
            category__slug=category
        )

    return render(
        request,
        "store/shop.html",
        {
            "products": products,
            "categories": categories,
            "search": search,
            "selected_category": category,
        }
    )


def product_detail(request, slug):

    product = get_object_or_404(
        Product,
        slug=slug,
        is_active=True
    )

    return render(
        request,
        "store/product_detail.html",
        {
            "product": product
        }
    )


def add_to_cart(request, product_id):
    if request.method != "POST":
        product = get_object_or_404(
            Product,
            id=product_id,
            is_active=True
        )
        return redirect("product_detail", slug=product.slug)

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True
    )

    if product.stock <= 0:
        return redirect("cart")

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    quantity = max(1, quantity)

    cart_data = request.session.get("cart", {})
    key = str(product.id)

    try:
        current_quantity = int(cart_data.get(key, 0))
    except (TypeError, ValueError):
        current_quantity = 0

    cart_data[key] = min(
        max(current_quantity, 0) + quantity,
        product.stock
    )

    request.session["cart"] = cart_data
    request.session.modified = True

    return redirect("cart")


def cart(request):
    cart_data = request.session.get("cart", {})
    cart_items = []
    subtotal = Decimal("0.00")
    updated_cart = {}

    for product_id, quantity in cart_data.items():
        try:
            product = Product.objects.get(
                id=int(product_id),
                is_active=True
            )
            quantity = int(quantity)
        except (Product.DoesNotExist, TypeError, ValueError):
            continue

        if product.stock <= 0 or quantity < 1:
            continue

        quantity = min(quantity, product.stock)

        updated_cart[str(product.id)] = quantity

        item_total = product.final_price * quantity
        subtotal += item_total

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "item_total": item_total,
        })

    if updated_cart != cart_data:
        request.session["cart"] = updated_cart
        request.session.modified = True

    return render(
        request,
        "store/cart.html",
        {
            "cart_items": cart_items,
            "subtotal": subtotal,
        }
    )


def update_cart(request, product_id):
    if request.method != "POST":
        return redirect("cart")

    cart_data = request.session.get("cart", {})
    key = str(product_id)

    if key not in cart_data:
        return redirect("cart")

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True
    )

    if product.stock <= 0:
        cart_data.pop(key, None)
    else:
        try:
            quantity = int(request.POST.get("quantity", 1))
        except (TypeError, ValueError):
            quantity = 1

        quantity = max(1, quantity)
        cart_data[key] = min(quantity, product.stock)

    request.session["cart"] = cart_data
    request.session.modified = True

    return redirect("cart")


def remove_from_cart(request, product_id):
    if request.method != "POST":
        return redirect("cart")

    cart_data = request.session.get("cart", {})
    cart_data.pop(str(product_id), None)

    request.session["cart"] = cart_data
    request.session.modified = True

    return redirect("cart")


@login_required
def checkout(request):

    cart_data = request.session.get(
        "cart",
        {}
    )

    if not cart_data:
        return redirect("cart")

    # --------------------------------
    # GET - Show Checkout Page
    # --------------------------------

    cart_items = []
    subtotal = 0

    for product_id, quantity in cart_data.items():

        product = Product.objects.filter(
            id=product_id,
            is_active=True
        ).first()

        if not product:
            continue

        if product.stock <= 0:
            continue

        if quantity > product.stock:
            quantity = product.stock

        item_total = (
            product.final_price * quantity
        )

        subtotal += item_total

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "item_total": item_total,
        })

    if not cart_items:
        return redirect("cart")

    # --------------------------------
    # POST - Place Order
    # --------------------------------

    if request.method == "POST":

        customer_name = request.POST.get(
            "customer_name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        address = request.POST.get(
            "address",
            ""
        ).strip()

        city = request.POST.get(
            "city",
            ""
        ).strip()

        state = request.POST.get(
            "state",
            ""
        ).strip()

        pincode = request.POST.get(
            "pincode",
            ""
        ).strip()

        # --------------------------------
        # Validate Customer Details
        # --------------------------------

        if not all([
            customer_name,
            email,
            phone,
            address,
            city,
            state,
            pincode,
        ]):

            return render(
                request,
                "store/checkout.html",
                {
                    "cart_items": cart_items,
                    "subtotal": subtotal,
                    "error": "Please fill all required fields.",
                }
            )

        # --------------------------------
        # Database Transaction
        # --------------------------------

        try:

            with transaction.atomic():

                locked_items = []
                fresh_subtotal = 0

                # ----------------------------
                # Re-check Stock
                # ----------------------------

                for product_id, quantity in cart_data.items():

                    product = (
                        Product.objects
                        .select_for_update()
                        .filter(
                            id=product_id,
                            is_active=True
                        )
                        .first()
                    )

                    if not product:

                        raise ValueError(
                            "One of the products is no longer available."
                        )

                    if product.stock < quantity:

                        raise ValueError(
                            f"Only {product.stock} item(s) available for "
                            f"{product.name}."
                        )

                    item_total = (
                        product.final_price * quantity
                    )

                    fresh_subtotal += item_total

                    locked_items.append({
                        "product": product,
                        "quantity": quantity,
                        "item_total": item_total,
                    })

                # ----------------------------
                # Create Order
                # ----------------------------

                order = Order.objects.create(
                        customer=request.user,
                        customer_name=customer_name,
                        email=email,
                        phone=phone,
                        address=address,
                        city=city,
                        state=state,
                        pincode=pincode,
                        total_amount=fresh_subtotal,
                    )

                # ----------------------------
                # Create Order Items
                # + Reduce Stock
                # ----------------------------

                for item in locked_items:

                    product = item["product"]
                    quantity = item["quantity"]

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        price=product.final_price,
                        quantity=quantity,
                        item_total=item["item_total"],
                    )

                    # Reduce stock
                    product.stock -= quantity

                    product.save(
                        update_fields=[
                            "stock",
                            "updated_at",
                        ]
                    )

        except ValueError as error:

            return render(
                request,
                "store/checkout.html",
                {
                    "cart_items": cart_items,
                    "subtotal": subtotal,
                    "error": str(error),
                }
            )

        # --------------------------------
        # Clear Cart
        # --------------------------------

        request.session["cart"] = {}
        request.session.modified = True

        # --------------------------------
        # Order Success
        # --------------------------------

        return redirect(
            "order_success",
            order_id=order.id
        )

    # --------------------------------
    # Show Checkout Page
    # --------------------------------

    return render(
        request,
        "store/checkout.html",
        {
            "cart_items": cart_items,
            "subtotal": subtotal,
        }
    )
def order_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    return render(
        request,
        "store/order_success.html",
        {
            "order": order
        }
    )

@login_required
def order_history(request):

    orders = (
        Order.objects
        .filter(
            customer=request.user
        )
        .prefetch_related("items")
    )

    return render(
        request,
        "store/order_history.html",
        {
            "orders": orders,
        }
    )

def register(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        if not username or not email or not password:

            return render(
                request,
                "store/register.html",
                {
                    "error": "Please fill all required fields."
                }
            )

        if password != confirm_password:

            return render(
                request,
                "store/register.html",
                {
                    "error": "Passwords do not match."
                }
            )

        if User.objects.filter(
            username=username
        ).exists():

            return render(
                request,
                "store/register.html",
                {
                    "error": "Username already exists."
                }
            )

        if User.objects.filter(
            email=email
        ).exists():

            return render(
                request,
                "store/register.html",
                {
                    "error": "Email already registered."
                }
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        login(request, user)

        return redirect("home")

    return render(
        request,
        "store/register.html"
    )

def login_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(
                request,
                user
            )

            return redirect("home")

        return render(
            request,
            "store/login.html",
            {
                "error": "Invalid username or password."
            }
        )

    return render(
        request,
        "store/login.html"
    )


def logout_view(request):

    logout(request)

    return redirect("home")

@login_required
def add_to_wishlist(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True
    )

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "shop"
        )
    )


@login_required
def remove_from_wishlist(request, product_id):

    Wishlist.objects.filter(
        user=request.user,
        product_id=product_id
    ).delete()

    return redirect("wishlist")


@login_required
def wishlist(request):

    wishlist_items = (
        Wishlist.objects
        .filter(user=request.user)
        .select_related("product")
    )

    return render(
        request,
        "store/wishlist.html",
        {
            "wishlist_items": wishlist_items,
        }
    )
@login_required
def add_to_wishlist(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True
    )

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    return redirect("wishlist")