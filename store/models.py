from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):

    name = models.CharField(
        max_length=100
    )

    slug = models.SlugField(
        unique=True
    )

    description = models.TextField(
        blank=True
    )
    # Category model
    image = models.ImageField(
        upload_to="categories/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products"
    )

    name = models.CharField(
        max_length=200
    )

    slug = models.SlugField(
        unique=True
    )

    description = models.TextField()

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    discount_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    image = models.ImageField(
    upload_to="products/",
    blank=True,
    null=True
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    is_featured = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def final_price(self):

        if self.discount_price:
            return self.discount_price

        return self.price


class Order(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders",
        null=True,
        blank=True
    )

    customer_name = models.CharField(
        max_length=150
    )

    email = models.EmailField()

    phone = models.CharField(
        max_length=20
    )

    address = models.TextField()

    city = models.CharField(
        max_length=100
    )

    state = models.CharField(
        max_length=100
    )

    pincode = models.CharField(
        max_length=10
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    product_name = models.CharField(
        max_length=200
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    quantity = models.PositiveIntegerField()

    item_total = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
    
class Wishlist(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="wishlist_items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="wishlist_items"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_product_wishlist"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
