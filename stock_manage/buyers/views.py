from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.cache import never_cache
from functools import wraps
from .models import Buyer, CartItem, Order, OrderItem
from admin_panel.models import ProductVariant, Blogs, Contact
from django.utils import timezone
from django.db import transaction
from django.db.models import F
import random
import string


def buyer_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("buyer_id"):
            messages.error(request, "Please login to access this page", extra_tags="buyer")
            return redirect("by_login")
        return view_func(request, *args, **kwargs)
    return wrapper



def by_register(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if Buyer.objects.filter(email=email).exists():
            
            return redirect("by_register")

        buyer = Buyer(
            name=name,
            email=email,
            password=make_password(password)
        )
        buyer.save()

        
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
                messages.error(request, "Invalid password", extra_tags="buyer")

        except Buyer.DoesNotExist:
            messages.error(request, "Buyer not found", extra_tags="buyer")

    return render(request, "by_login.html")



@never_cache
def by_index(request):
    return render(request,'by_index.html')

@never_cache
def by_about(request):
    return render(request,'by_about.html')

@never_cache
def by_blog(request):
    blogs = Blogs.objects.all().order_by('-id')
    return render(request, 'by_blog.html', {
        'blogs': blogs
    })

@never_cache
def by_contact(request):
    if request.method == "POST":
        first_name = request.POST.get("fname", "").strip()
        last_name = request.POST.get("lname", "").strip()
        email = request.POST.get("email", "").strip()
        message_text = request.POST.get("message", "").strip()

        if first_name and email and message_text:
            Contact.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                message=message_text,
            )
            messages.success(request, "Your message has been sent successfully.")
        else:
            messages.error(request, "Please fill all required fields.")

        return redirect("by_contact")

    return render(request, 'by_contact.html')

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
        
        return redirect("by_login")

    try:
        buyer = Buyer.objects.get(id=buyer_id)
    except Buyer.DoesNotExist:
        
        return redirect("by_login")

    try:
        variant = ProductVariant.objects.get(id=variant_id, product__status=True)
    except ProductVariant.DoesNotExist:
        
        return redirect("by_shop")

    cart_item, created = CartItem.objects.get_or_create(
        buyer=buyer,
        variant=variant,
        defaults={"quantity": 1},
    )

    if created:
        
        cart_item.quantity = 1
        cart_item.save()
    else:
        
        if cart_item.quantity < variant.stock:
            cart_item.quantity += 1
            cart_item.save()
        else:
            
            return redirect("by_shop")

    
    return redirect("by_cart")


@never_cache
@buyer_login_required
def by_cart(request):
    buyer_id = request.session.get("buyer_id")
    buyer = Buyer.objects.get(id=buyer_id)


    if request.method == "POST":
        for item in CartItem.objects.filter(buyer=buyer):
            quantity_key = f"quantity_{item.id}"
            if quantity_key in request.POST:
                try:
                    new_quantity = int(request.POST.get(quantity_key))
                    
                    if new_quantity < 1:
                        new_quantity = 1
                    
                    
                    if new_quantity <= item.variant.stock:
                        item.quantity = new_quantity
                        item.save()
                    else:
                       
                        item.quantity = item.variant.stock
                        item.save()
                        
                except ValueError:
                    
                    item.quantity = 1
                    item.save()
        return redirect("by_cart")

    cart_items = CartItem.objects.select_related(
        "variant",
        "variant__product"
    ).filter(buyer=buyer)

    subtotal = 0
    for item in cart_items:
       
        if item.quantity < 1:
            item.quantity = 1
            item.save()
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
    buyer_id = request.session.get("buyer_id")
    buyer = Buyer.objects.get(id=buyer_id)
    
    cart_items = CartItem.objects.select_related(
        "variant",
        "variant__product"
    ).filter(buyer=buyer)
    
    if not cart_items.exists():
        
        return redirect("by_cart")
    
    subtotal = 0
    for item in cart_items:
        if item.quantity < 1:
            item.quantity = 1
            item.save()
        item.total_price = float(item.variant.price) * item.quantity
        subtotal += item.total_price
    
    context = {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "total": subtotal,
        "buyer": buyer,
    }
    
    return render(request, 'by_checkout.html', context)


def generate_order_number():
    """Generate unique order number"""
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD-{timestamp}-{random_str}"


@never_cache
@buyer_login_required
def place_order(request):
    if request.method != "POST":
        return redirect("by_checkout")
    
    buyer_id = request.session.get("buyer_id")
    buyer = Buyer.objects.get(id=buyer_id)
    cart_items = CartItem.objects.select_related("variant", "variant__product").filter(buyer=buyer)
    if not cart_items.exists():
        return redirect("by_cart")
    for item in cart_items:
        if item.quantity > item.variant.stock:
            return redirect("by_checkout")
    first_name = request.POST.get("c_fname", "").strip()
    last_name = request.POST.get("c_lname", "").strip()
    company_name = request.POST.get("c_companyname", "").strip()
    email = request.POST.get("c_email_address", "").strip()
    phone = request.POST.get("c_phone", "").strip()
    address = request.POST.get("c_address", "").strip()
    address_line2 = request.POST.get("c_address_line2", "").strip()
    state_city = request.POST.get("c_state_country", "").strip()
    postal_code = request.POST.get("c_postal_zip", "").strip()
    country = request.POST.get("c_country", "").strip()
    payment_method = request.POST.get("payment_method", "cash_on_delivery")
    order_notes = request.POST.get("c_order_notes", "").strip()
    ship_to_different = request.POST.get("c_ship_different_address") == "1"
    if not all([first_name, last_name, email, phone, address, state_city, postal_code, country]):
        return redirect("by_checkout")
    subtotal = sum(item.variant.price * item.quantity for item in cart_items)
    total = subtotal
    try:
        with transaction.atomic():
            order_number = generate_order_number()
            order = Order.objects.create(
                buyer=buyer,
                order_number=order_number,
                first_name=first_name,
                last_name=last_name,
                company_name=company_name if company_name else None,
                email=email,
                phone=phone,
                address=address,
                address_line2=address_line2 if address_line2 else None,
                city=state_city,
                state=state_city,
                postal_code=postal_code,
                country=country,
                ship_to_different_address=ship_to_different,
                subtotal=subtotal,
                total=total,
                payment_method=payment_method,
                order_notes=order_notes if order_notes else None,
            )
            if ship_to_different:
                shipping_first_name = request.POST.get("c_diff_fname", "").strip()
                shipping_last_name = request.POST.get("c_diff_lname", "").strip()
                shipping_company_name = request.POST.get("c_diff_companyname", "").strip()
                shipping_address = request.POST.get("c_diff_address", "").strip()
                shipping_address_line2 = request.POST.get("c_diff_address_line2", "").strip()
                shipping_state_city = request.POST.get("c_diff_state_country", "").strip()
                shipping_postal_code = request.POST.get("c_diff_postal_zip", "").strip()
                shipping_country = request.POST.get("c_diff_country", "").strip()
                if all([shipping_first_name, shipping_last_name, shipping_address, shipping_state_city, shipping_postal_code, shipping_country]):
                    order.shipping_first_name = shipping_first_name
                    order.shipping_last_name = shipping_last_name
                    order.shipping_company_name = shipping_company_name if shipping_company_name else None
                    order.shipping_address = shipping_address
                    order.shipping_address_line2 = shipping_address_line2 if shipping_address_line2 else None
                    order.shipping_city = shipping_state_city
                    order.shipping_state = shipping_state_city
                    order.shipping_postal_code = shipping_postal_code
                    order.shipping_country = shipping_country
                    order.save()
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    variant=item.variant,
                    product_name=item.variant.product.name,
                    quantity=item.quantity,
                    price=item.variant.price,
                    total=item.variant.price * item.quantity
                )
                updated = ProductVariant.objects.filter(id=item.variant_id, stock__gte=item.quantity).update(stock=F('stock') - item.quantity)
                if not updated:
                    raise ValueError("Insufficient stock")
            cart_items.delete()
    except Exception:
        return redirect("by_checkout")
    return redirect("by_thankyou")

@never_cache
@buyer_login_required
def by_history(request):
    buyer_id = request.session.get("buyer_id")
    buyer = Buyer.objects.get(id=buyer_id)
    
    orders = Order.objects.filter(buyer=buyer).prefetch_related(
        "items",
        "items__variant",
        "items__variant__product"
    ).order_by("-created_at")
    status_counts = {
        "all": orders.count(),
        "pending": orders.filter(status="pending").count(),
        "processing": orders.filter(status="processing").count(),
        "shipped": orders.filter(status="shipped").count(),
        "delivered": orders.filter(status="delivered").count(),
        "cancelled": orders.filter(status="cancelled").count(),
    }
    return render(request, 'by_history.html', {
        "orders": orders,
        "status_counts": status_counts
    })




@never_cache
@buyer_login_required
def by_thankyou(request):
    return render(request,'by_thankyou.html')

@never_cache
@buyer_login_required
def by_cancel_order(request, order_id):
    if request.method != "POST":
        return redirect("by_history")
    buyer_id = request.session.get("buyer_id")
    try:
        order = Order.objects.select_related("buyer").prefetch_related(
            "items",
            "items__variant"
        ).get(id=order_id, buyer_id=buyer_id)
    except Order.DoesNotExist:
        
        return redirect("by_history")
    if order.status not in ("pending", "processing"):
        
        return redirect("by_history")
    for item in order.items.all():
        ProductVariant.objects.filter(id=item.variant_id).update(stock=F('stock') + item.quantity)
    order.status = "cancelled"
    order.save()
    messages.success(request, "Your order has been cancelled.")
    return redirect("by_history")

@never_cache
@buyer_login_required
def by_return_order(request, order_id):
    if request.method != "POST":
        return redirect("by_history")
    buyer_id = request.session.get("buyer_id")
    try:
        order = Order.objects.select_related("buyer").prefetch_related(
            "items",
            "items__variant"
        ).get(id=order_id, buyer_id=buyer_id)
    except Order.DoesNotExist:
        return redirect("by_history")
    if order.status != "delivered":
        return redirect("by_history")
    order.status = "return_requested"
    order.save()
    messages.success(request, "Return request submitted. Supplier will verify shortly.")
    return redirect("by_history")


def by_logout(request):
    request.session.pop("buyer_id", None)
    request.session.pop("buyer_name", None)
    request.session.pop("buyer_email", None)
    messages.success(request, "Logged out successfully.", extra_tags="buyer")
    return redirect('by_index')

