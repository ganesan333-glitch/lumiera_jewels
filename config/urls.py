from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from store.views import (
    home,
    shop,
    product_detail,
    add_to_cart,
    cart,
    update_cart,
    remove_from_cart,
    checkout,
    order_success,
    order_history,
    register,
    login_view,
    logout_view,
    wishlist,
    add_to_wishlist,
    remove_from_wishlist,
)


urlpatterns = [

    path(
        "admin/",
        admin.site.urls
    ),

    path(
        "",
        home,
        name="home"
    ),

    path(
        "shop/",
        shop,
        name="shop"
    ),

    path(
        "product/<slug:slug>/",
        product_detail,
        name="product_detail"
    ),

    path(
        "cart/add/<int:product_id>/",
        add_to_cart,
        name="add_to_cart"
    ),

    path(
        "cart/",
        cart,
        name="cart"
    ),

    path(
        "cart/update/<int:product_id>/",
        update_cart,
        name="update_cart"
    ),

    path(
        "cart/remove/<int:product_id>/",
        remove_from_cart,
        name="remove_from_cart"
    ),

    path(
        "checkout/",
        checkout,
        name="checkout"
    ),

    path(
        "order-success/<int:order_id>/",
        order_success,
        name="order_success"
    ),

    path(
        "orders/",
        order_history,
        name="order_history"
    ),

    # Authentication

    path(
        "register/",
        register,
        name="register"
    ),

    path(
        "login/",
        login_view,
        name="login"
    ),

    path(
        "logout/",
        logout_view,
        name="logout"
    ),
    path(
    "wishlist/",
    wishlist,
    name="wishlist"
),

path(
    "wishlist/add/<int:product_id>/",
    add_to_wishlist,
    name="add_to_wishlist"
),

path(
    "wishlist/remove/<int:product_id>/",
    remove_from_wishlist,
    name="remove_from_wishlist"
),
]
urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )