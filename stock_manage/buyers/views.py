from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.cache import never_cache
from functools import wraps
from .models import Buyer, CartItem, Order, OrderItem
from admin_panel.models import ProductVariant, Blogs, Contact
from django.utils import timezone
from django.db import transaction
from django.db.models import F, OuterRef, Subquery, Sum
from django.core.paginator import Paginator
import random
import string
from django.http import JsonResponse


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
def by_home(request):
    return render(request, 'by_home.html')

@never_cache
def by_product(request, variant_id):
    try:
        variant = ProductVariant.objects.select_related(
            'product',
            'product__brand',
            'product__brand__subcetegory',
            'product__brand__subcetegory__category',
            'color',
            'size'
        ).get(id=variant_id, product__status=True)
    except ProductVariant.DoesNotExist:
        return redirect('by_shop')
    product = variant.product
    gallery = list(getattr(product, 'images', []).all()) if hasattr(product, 'images') else []
    variants = ProductVariant.objects.select_related('color', 'size').filter(product=product)
    colors = {}
    sizes = {}
    for v in variants:
        colors.setdefault(v.color.id, {'id': v.color.id, 'name': v.color.name, 'variants': []})
        sizes.setdefault(v.size.id, {'id': v.size.id, 'name': v.size.name, 'variants': []})
        colors[v.color.id]['variants'].append(v.id)
        sizes[v.size.id]['variants'].append(v.id)
    specs = []
    try:
        from admin_panel.models import VariantSpec
        specs = list(VariantSpec.objects.filter(variant=variant).values('name', 'value'))
    except Exception:
        specs = []
    discount_percent = None
    try:
        if product.base_price and product.base_price > variant.price:
            discount_percent = int(round((float(product.base_price) - float(variant.price)) / float(product.base_price) * 100))
    except Exception:
        discount_percent = None
    context = {
        'variant': variant,
        'product': product,
        'gallery': gallery,
        'colors': colors.values(),
        'sizes': sizes.values(),
        'specs': specs,
        'discount_percent': discount_percent,
    }
    return render(request, 'by_product.html', context)
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
def by_shop(request):
    base_qs = ProductVariant.objects.select_related(
        'product',
        'product__brand',
        'product__brand__subcetegory',
        'product__brand__subcetegory__category'
    ).filter(
        product__status=True,
        stock__gt=0
    ).order_by('-id')

    price_min = base_qs.order_by('price').values_list('price', flat=True).first() or 0
    price_max = base_qs.order_by('-price').values_list('price', flat=True).first() or 0

    category_id = request.GET.get('category')
    min_price = request.GET.get('min')
    max_price = request.GET.get('max')
    brands_selected = request.GET.getlist('brands')
    sort = request.GET.get('sort') or 'recommended'

    qs = base_qs
    if category_id:
        qs = qs.filter(product__brand__subcetegory__category_id=category_id)
        price_min = qs.order_by('price').values_list('price', flat=True).first() or price_min
        price_max = qs.order_by('-price').values_list('price', flat=True).first() or price_max
    if min_price:
        try:
            qs = qs.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            qs = qs.filter(price__lte=float(max_price))
        except ValueError:
            pass
    if brands_selected:
        qs = qs.filter(product__brand__id__in=brands_selected)

    raw_categories = list(base_qs.values('product__brand__subcetegory__category__id', 'product__brand__subcetegory__category__name').distinct())
    seen_cat_names = set()
    categories = []
    for c in raw_categories:
        cn = (c.get('product__brand__subcetegory__category__name') or '').strip().lower()
        if cn in seen_cat_names:
            continue
        seen_cat_names.add(cn)
        categories.append({
            'id': c.get('product__brand__subcetegory__category__id'),
            'name': c.get('product__brand__subcetegory__category__name')
        })
    raw_brands = list(qs.values('product__brand__id', 'product__brand__name').distinct())
    seen_names = set()
    brands = []
    for b in raw_brands:
        n = (b.get('product__brand__name') or '').strip().lower()
        if n in seen_names:
            continue
        seen_names.add(n)
        brands.append(b)

    sales_sub = Subquery(
        OrderItem.objects.filter(variant_id=OuterRef('pk'))
        .values('variant_id')
        .annotate(s=Sum('quantity'))
        .values('s')[:1]
    )
    qs = qs.annotate(sales=sales_sub)
    if sort == 'best':
        qs = qs.order_by(F('sales').desc(nulls_last=True))
    elif sort == 'price_asc':
        qs = qs.order_by('price')
    elif sort == 'price_desc':
        qs = qs.order_by('-price')
    else:
        qs = qs.order_by('-id')

    top_sellers = OrderItem.objects.values('variant_id').annotate(s=Sum('quantity')).order_by('-s')[:12]
    best_ids = {row['variant_id'] for row in top_sellers}

    paginator = Paginator(qs, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'by_shop.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'total': qs.count(),
        'categories': categories,
        'brands': brands,
        'brands_selected': brands_selected,
        'sort': sort,
        'best_ids': best_ids,
        'selected_category': category_id,
        'price_min': price_min,
        'price_max': price_max,
        'selected_min_price': min_price or price_min,
        'selected_max_price': max_price or price_max,
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

    quantity_to_add = 1
    if request.method == "POST":
        try:
            qty = int(request.POST.get("quantity", "1"))
            if qty > 0:
                quantity_to_add = qty
        except Exception:
            quantity_to_add = 1

    cart_item, created = CartItem.objects.get_or_create(
        buyer=buyer,
        variant=variant,
        defaults={"quantity": 1},
    )

    if created:
        
        cart_item.quantity = min(quantity_to_add, variant.stock if variant.stock else quantity_to_add)
        cart_item.save()
    else:
        
        if cart_item.quantity < variant.stock:
            cart_item.quantity = min(cart_item.quantity + quantity_to_add, variant.stock)
            cart_item.save()
        else:
            
            return redirect("by_shop")

    
    return redirect("by_cart")


@never_cache
def add_to_wishlist(request, variant_id):
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
    from .models import WishlistItem
    WishlistItem.objects.get_or_create(buyer=buyer, variant=variant)
    return redirect("by_product", variant_id=variant.id)


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
        cart_items = CartItem.objects.select_related(
            "variant",
            "variant__product"
        ).filter(buyer=buyer)
        subtotal = 0
        items_payload = []
        for item in cart_items:
            if item.quantity < 1:
                item.quantity = 1
                item.save()
            item.total_price = item.variant.price * item.quantity
            subtotal += item.total_price
            items_payload.append({
                "id": item.id,
                "quantity": item.quantity,
                "line_total": float(item.total_price),
            })
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "subtotal": float(subtotal),
                "total": float(subtotal),
                "items": items_payload
            })
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


@never_cache
@buyer_login_required
def by_update_profile(request):
    if request.method != "POST":
        return redirect("by_index")
    buyer_id = request.session.get("buyer_id")
    try:
        buyer = Buyer.objects.get(id=buyer_id)
    except Buyer.DoesNotExist:
        return redirect("by_login")
    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()
    gender = request.POST.get("gender", "").strip()
    phone = request.POST.get("phone", "").strip()
    address = request.POST.get("address", "").strip()
    profile_image = request.FILES.get("profile_image")
    if name:
        buyer.name = name
    if email and email != buyer.email:
        if Buyer.objects.filter(email=email).exclude(id=buyer.id).exists():
            messages.error(request, "Email already in use.", extra_tags="buyer")
            referer = request.META.get("HTTP_REFERER") or "/buyers/"
            return redirect(referer)
        buyer.email = email
    if gender:
        buyer.gender = gender
    if phone:
        buyer.phone = phone
    if address:
        buyer.address = address
    if profile_image:
        buyer.profile_image = profile_image
    buyer.save()
    request.session["buyer_name"] = buyer.name
    request.session["buyer_email"] = buyer.email
    messages.success(request, "Profile updated successfully.", extra_tags="buyer")
    referer = request.META.get("HTTP_REFERER") or "/buyers/"
    return redirect(referer)

