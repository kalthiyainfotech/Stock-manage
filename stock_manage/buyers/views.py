from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .models import Buyer
from django.views.decorators.cache import never_cache



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
                request.session["buyer_email"] = buyer.email
                return redirect("by_dash")
            else:
                messages.error(request, "Invalid password")
        except Buyer.DoesNotExist:
            messages.error(request, "Buyer not found")

    return render(request, "by_login.html")


@never_cache
def by_dash(request):
    return render(request,'by_dash.html')


def by_logout(request):
    if 'by_id' in request.session:
        by_name = request.session.get('by_name', '')
        request.session.flush()
        messages.success(request, f"Logged out successfully. Goodbye, {by_name}!")
    return redirect('by_login')

