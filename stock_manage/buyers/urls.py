from django.urls import path
from buyers.views import *

urlpatterns = [
    path("", by_index, name="by_index"),
    path("login/", by_login, name="by_login"),
    path("register/", by_register, name="by_register"),
    path("about-us/", by_about, name="by_about"),
    path("blog/", by_blog, name="by_blog"),
    path("cart/", by_cart, name="by_cart"),
    path("cart/add/<int:variant_id>/", add_to_cart, name="by_add_to_cart"),
    path("checkout/", by_checkout, name="by_checkout"),
    path("contact/", by_contact, name="by_contact"),
    path("services/", by_services, name="by_services"),
    path("shop/", by_shop, name="by_shop"),
    path("thankyou/", by_thankyou, name="by_thankyou"),
    path("logout/", by_logout, name="by_logout"),
    path("cart/remove/<int:item_id>/", remove_from_cart, name="by_remove_from_cart"),
    path("checkout/place-order/", place_order, name="by_place_order"),
    path("history/", by_history, name="by_history"),
    path("order/<int:order_id>/return/", by_return_order, name="by_return_order"),
    path("order/<int:order_id>/cancel/", by_cancel_order, name="by_cancel_order"),
]
