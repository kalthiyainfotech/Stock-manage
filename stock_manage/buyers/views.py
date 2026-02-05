from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.cache import never_cache
from functools import wraps

from .models import Buyer


def buyer_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("buyer_id"):
            messages.error(request, "Please login first")
            return redirect("by_login")
        return view_func(request, *args, **kwargs)
    return wrapper



def by_register(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if Buyer.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect("by_register")

        buyer = Buyer(
            name=name,
            email=email,
            password=make_password(password)
        )
        buyer.save()

        messages.success(request, "Registration successful. Please login.")
        return redirect("by_login")

    return render(request, "by_register.html")


def by_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            buyer = Buyer.objects.get(email=email)

            if check_password(password, buyer.password):
                request.session["buyer_id"] = buyer.id
                request.session["buyer_name"] = buyer.name
                request.session["buyer_email"] = buyer.email
                return redirect("by_index")

            else:
                messages.error(request, "Invalid password")

        except Buyer.DoesNotExist:
            messages.error(request, "Buyer not found")

    return render(request, "by_login.html")



@never_cache
def by_index(request):
    return render(request,'by_index.html')

@never_cache
def by_about(request):
    return render(request,'by_about.html')

@never_cache
def by_blog(request):
    return render(request,'by_blog.html')

@never_cache
def by_contact(request):
    return render(request,'by_contact.html')

@never_cache
def by_services(request):
    return render(request,'by_services.html')

@never_cache
def by_shop(request):
    return render(request,'by_shop.html')


@never_cache
@buyer_login_required
def by_cart(request):
    return render(request,'by_cart.html')


@never_cache
@buyer_login_required
def by_checkout(request):
    return render(request,'by_checkout.html')


@never_cache
@buyer_login_required
def by_thankyou(request):
    return render(request,'by_thankyou.html')


def by_logout(request):
    request.session.flush()
    return redirect('by_index')

