from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.cache import never_cache
from functools import wraps
from .models import Buyer, CartItem
from admin_panel.models import ProductVariant


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
    products = ProductVariant.objects.select_related(
        'product',
        'product__brand',
        'product__brand__subcetegory',
        'product__brand__subcetegory__category'
    ).filter(
        product__status=True,
        stock__gt=0
    ).order_by('-id')

    return render(request, 'by_shop.html', {
        'products': products
    })


@never_cache
def add_to_cart(request, variant_id):
    buyer_id = request.session.get("buyer_id")
    if not buyer_id:
        messages.error(request, "Please login to add items to your cart.")
        return redirect("by_login")

    try:
        buyer = Buyer.objects.get(id=buyer_id)
    except Buyer.DoesNotExist:
        messages.error(request, "Buyer not found. Please login again.")
        return redirect("by_login")

    try:
        variant = ProductVariant.objects.get(id=variant_id, product__status=True)
    except ProductVariant.DoesNotExist:
        messages.error(request, "Product not found.")
        return redirect("by_shop")

    cart_item, created = CartItem.objects.get_or_create(
        buyer=buyer,
        variant=variant,
        defaults={"quantity": 1},
    )

    if not created:
        
        if cart_item.quantity < variant.stock:
            cart_item.quantity += 1
            cart_item.save()
        else:
            messages.warning(request, "No more stock available for this product.")
            return redirect("by_shop")

    messages.success(request, "Product added to cart.")
    return redirect("by_cart")


@never_cache
@buyer_login_required
def by_cart(request):
    buyer_id = request.session.get("buyer_id")
    buyer = Buyer.objects.get(id=buyer_id)

    cart_items = CartItem.objects.select_related(
        "variant",
        "variant__product"
    ).filter(buyer=buyer)

    subtotal = 0
    for item in cart_items:
        item.total_price = item.variant.price * item.quantity
        subtotal += item.total_price

    context = {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "total": subtotal,  
    }

    return render(request, "by_cart.html", context)


@never_cache
@buyer_login_required
def remove_from_cart(request, item_id):
    buyer_id = request.session.get("buyer_id")
    CartItem.objects.filter(id=item_id, buyer_id=buyer_id).delete()
    return redirect("by_cart")


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

