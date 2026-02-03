from django.urls import path
from buyers.views import *

urlpatterns = [
    path("", by_login, name="by_login"),
    path("register/", by_register, name="by_register"),
    path("home/", by_dash, name="by_dash"),
    path("logout/", by_logout, name="by_logout"),
]
