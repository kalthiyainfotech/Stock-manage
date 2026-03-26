import razorpay
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.cache import never_cache
from functools import wraps
from .models import Buyer, CartItem, Order, OrderItem, WishlistItem
from admin_panel.models import ProductVariant, ProductImage, Blogs, Contact
from django.utils import timezone
from django.db import transaction
from django.db.models import F, OuterRef, Subquery, Sum, Q, Max
from django.core.paginator import Paginator
import random
import string
from django.http import JsonResponse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def buyer_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("buyer_id"):
            messages.error(request, "Please login to access this page", extra_tags="buyer")
            return redirect("by_login")
        return view_func(request, *args, **kwargs)
    return wrapper

def _safe_image_url(image_field):
    try:
        if not image_field:
            return None
        name = getattr(image_field, "name", None)
        storage = getattr(image_field, "storage", None)
        if not name or not storage:
            return None
        if not storage.exists(name):
            return None
        return image_field.url
    except Exception:
        return None

def _resolve_shop_image_url(product, variant=None):
    image_url = _safe_image_url(getattr(product, "image", None))
    if image_url:
        return image_url
    if variant is not None:
        image_url = _safe_image_url(getattr(variant, "image", None))
        if image_url:
            return image_url
    try:
        other_v = ProductVariant.objects.filter(
            product=product,
            image__isnull=False
        ).exclude(image='').order_by('-id').first()
        image_url = _safe_image_url(getattr(other_v, "image", None)) if other_v else None
        if image_url:
            return image_url
    except Exception:
        pass
    try:
        product_img = ProductImage.objects.filter(product=product).order_by("id").first()
        image_url = _safe_image_url(getattr(product_img, "image", None)) if product_img else None
        if image_url:
            return image_url
    except Exception:
        pass
    return None

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
    from admin_panel.models import Category, Product, ProductImage
    categories_qs = Category.objects.filter(status=True).order_by('name')
    cards = []
    for c in categories_qs:
        image_url = None
        p = Product.objects.filter(brand__subcetegory__category=c, status=True).order_by('-id').first()
        if p and p.image:
            try:
                image_url = p.image.url
            except Exception:
                image_url = None
        if not image_url and p:
            pi = ProductImage.objects.filter(product=p).order_by('-id').first()
            if pi and pi.image:
                try:
                    image_url = pi.image.url
                except Exception:
                    image_url = None
        cards.append({
            'id': c.id,
            'name': c.name,
            'image_url': image_url
        })
    return render(request,'by_index.html', {'home_categories': cards})

@never_cache
def by_blog(request):
    blogs = Blogs.objects.all().order_by('-id')
    return render(request, 'by_blog.html', {
        'blogs': blogs,
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
    # extra info maps to support UI logic
    variants_info = {}
    size_map = {}
    for v in variants:
        colors.setdefault(v.color.id, {'id': v.color.id, 'name': v.color.name, 'variants': []})
        sizes.setdefault(v.size.id, {'id': v.size.id, 'name': v.size.name, 'variants': []})
        colors[v.color.id]['variants'].append(v.id)
        sizes[v.size.id]['variants'].append(v.id)
        variants_info[v.id] = {
            'id': v.id,
            'color_id': v.color.id,
            'size_id': v.size.id,
            'stock': v.stock,
            'price': float(v.price),
            'image_url': _safe_image_url(getattr(v, 'image', None)) or '',
        }
        size_map.setdefault(v.color.id, {}).setdefault(v.size.id, {'id': v.id, 'stock': v.stock})

    def _valid_color_entry(entry):
        n = (entry.get('name') or '').strip().lower()
        return bool(n) and n != 'default'

    visible_colors = {cid: c for cid, c in colors.items() if _valid_color_entry(c)}

    from admin_panel.models import VariantImage
    
    gallery_annotated = []
    # Add Product generic gallery mapped to all colors as fallback
    all_cids = list(visible_colors.keys())
    
    seen_urls = {} # url -> entry in gallery_annotated

    def add_to_annotated(url, color_ids, is_main=False):
        if not url: return
        
        # Consistent URL for keying
        url_key = url.strip()
        file_name = url_key.split('/')[-1].split('?')[0] # Remove query params if any
        
        existing = seen_urls.get(url_key)
        if not existing:
            # Fallback: check if another entry has the same filename (different URL format/relative vs absolute)
            for key, entry in seen_urls.items():
                if key.split('/')[-1].split('?')[0] == file_name:
                    existing = entry
                    break

        if existing:
            # update existing entry color_ids
            existing_cids = set(existing['color_ids'])
            existing_cids.update(color_ids)
            existing['color_ids'] = list(existing_cids)
            if is_main: 
                existing['is_main'] = True
        else:
            entry = {
                'url': url,
                'color_ids': list(set(color_ids)),
                'is_main': is_main
            }
            gallery_annotated.append(entry)
            seen_urls[url_key] = entry

    # 1. Variant specific images (Color-based)
    variant_processed = set()
    for v in variants:
        cid = v.color.id
        if cid not in all_cids: continue
        
        # Group by (color, image_path) to avoid duplicate calls for same physical file
        v_main_url = _safe_image_url(getattr(v, 'image', None))
        if v_main_url:
            add_to_annotated(v_main_url, [cid], is_main=True)
        
        # For gallery images, we also group by variant set or just rely on add_to_annotated merging
        for vi in v.gallery_images.all():  # Use related_name 'gallery_images'
            v_gallery_url = _safe_image_url(getattr(vi, 'image', None))
            if v_gallery_url:
                add_to_annotated(v_gallery_url, [cid])

    # 2. Main Product Image (Default)
    product_main_url = _safe_image_url(getattr(product, 'image', None))
    if product_main_url:
        # Check if this main image belongs to a specific variant color
        matched_color_ids = []
        p_img_name = product.image.name.split('/')[-1]
        for v in variants:
            if v.image:
                v_img_name = v.image.name.split('/')[-1]
                if v_img_name == p_img_name:
                    if v.color.id in all_cids:
                        matched_color_ids.append(v.color.id)
        
        # If it matches specific variants, only show for those colors.
        # Otherwise, it's a generic product image, show for all.
        target_cids = list(set(matched_color_ids)) if matched_color_ids else all_cids
        if target_cids:
            # Only mark as main if no variant-specific image was already added as main for these colors
            # Actually, add_to_annotated handles the is_main flag.
            add_to_annotated(product_main_url, target_cids, is_main=True)

    # 3. Extra Product generic images - shown for all colors
    for img in gallery:
        try:
            product_gallery_url = _safe_image_url(getattr(img, 'image', None))
            if product_gallery_url:
                add_to_annotated(product_gallery_url, all_cids)
        except Exception:
            pass
    
    # Optional backward-compatible dictionary depending on template structure
    images_by_color = {cid: [] for cid in visible_colors.keys()}
    for item in gallery_annotated:
        for cid in item.get('color_ids', []):
            if cid in images_by_color:
                images_by_color[cid].append(item['url'])
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
    initial_main_image_url = product_main_url or _safe_image_url(getattr(variant, 'image', None))
    if not initial_main_image_url and gallery_annotated:
        color_matched = next((g for g in gallery_annotated if variant.color.id in g.get('color_ids', [])), None)
        initial_main_image_url = (color_matched or gallery_annotated[0]).get('url')

    # Fetch Related Products (same category)
    related_products_qs = ProductVariant.objects.select_related(
        'product', 'product__brand'
    ).filter(
        product__brand__subcetegory__category=product.brand.subcetegory.category,
        product__status=True,
        stock__gt=0
    ).exclude(product=product).values('product_id').annotate(first_id=Max('id')).values('first_id')

    related_variants = ProductVariant.objects.select_related(
        'product', 'product__brand'
    ).filter(id__in=related_products_qs)[:10]

    for rv in related_variants:
        rv.calculated_image_url = _resolve_shop_image_url(rv.product, rv)

    # Fetch Reviews
    from .models import ProductReview
    reviews = ProductReview.objects.filter(variant__product=product).select_related('buyer')
    
    # Check if current user can review (must have purchased the product and not reviewed yet)
    can_review = False
    buyer_id = request.session.get("buyer_id")
    if buyer_id:
        has_purchased = OrderItem.objects.filter(
            order__buyer_id=buyer_id, 
            variant__product=product,
            order__status='delivered'
        ).exists()
        has_reviewed = ProductReview.objects.filter(buyer_id=buyer_id, variant__product=product).exists()
        if has_purchased and not has_reviewed:
            can_review = True

    context = {
        'variant': variant,
        'product': product,
        'gallery': gallery,
        'colors': visible_colors.values(),
        'sizes': sizes.values(),
        'specs': specs,
        'discount_percent': discount_percent,
        'variants_info': variants_info,
        'size_map': size_map,
        'images_by_color': images_by_color,
        'gallery_annotated': gallery_annotated,
        'initial_main_image_url': initial_main_image_url,
        'related_products': related_variants,
        'reviews': reviews,
        'can_review': can_review,
    }
    return render(request, 'by_product.html', context)

@never_cache
@buyer_login_required
def add_review(request, variant_id):
    from .models import ProductReview
    if request.method == "POST":
        buyer_id = request.session.get("buyer_id")
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")
        
        try:
            variant = ProductVariant.objects.get(id=variant_id)
            # Check if already reviewed for this product
            if ProductReview.objects.filter(buyer_id=buyer_id, variant__product=variant.product).exists():
                messages.error(request, "You have already reviewed this product.")
            else:
                ProductReview.objects.create(
                    buyer_id=buyer_id,
                    variant=variant,
                    rating=rating,
                    comment=comment
                )
                messages.success(request, "Thank you for your review!")
        except Exception as e:
            messages.error(request, f"Error adding review: {str(e)}")
            
    return redirect(request.META.get('HTTP_REFERER', 'by_index'))

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
    unique_variant_ids = ProductVariant.objects.filter(
        product__status=True,
        stock__gt=0
    ).values('product_id').annotate(first_id=Max('id')).values('first_id')

    base_qs = ProductVariant.objects.select_related(
        'product',
        'product__brand',
        'product__brand__subcetegory',
        'product__brand__subcetegory__category'
    ).filter(
        id__in=unique_variant_ids
    ).order_by('-id')

    price_min = base_qs.order_by('price').values_list('price', flat=True).first() or 0
    price_max = base_qs.order_by('-price').values_list('price', flat=True).first() or 0

    category_id = request.GET.get('category')
    q = (request.GET.get('q') or '').strip()
    min_price = request.GET.get('min')
    max_price = request.GET.get('max')
    brands_selected = request.GET.getlist('brands')
    sort = request.GET.get('sort') or 'recommended'

    qs = base_qs
    if category_id:
        qs = qs.filter(product__brand__subcetegory__category_id=category_id)
        price_min = qs.order_by('price').values_list('price', flat=True).first() or price_min
        price_max = qs.order_by('-price').values_list('price', flat=True).first() or price_max
    if q:
        qs = qs.filter(
            Q(product__name__icontains=q) |
            Q(product__brand__name__icontains=q)
        )
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

    buyer_id = request.session.get('buyer_id')
    wishlist_ids = set()
    if buyer_id:
        wishlist_ids = set(WishlistItem.objects.filter(buyer_id=buyer_id).values_list('variant_id', flat=True))

    paginator = Paginator(qs, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    for item in page_obj:
        item.calculated_image_url = _resolve_shop_image_url(item.product, item)

    return render(request, 'by_shop.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'total': qs.count(),
        'categories': categories,
        'brands': brands,
        'brands_selected': brands_selected,
        'sort': sort,
        'best_ids': best_ids,
        'wishlist_ids': wishlist_ids,
        'selected_category': category_id,
        'q': q,
        'price_min': price_min,
        'price_max': price_max,
        'selected_min_price': min_price or price_min,
        'selected_max_price': max_price or price_max,
    })

@never_cache
def by_shop_api(request):
    unique_variant_ids = ProductVariant.objects.filter(
        product__status=True,
        stock__gt=0
    ).values('product_id').annotate(first_id=Max('id')).values('first_id')

    base_qs = ProductVariant.objects.select_related(
        'product',
        'product__brand',
        'product__brand__subcetegory',
        'product__brand__subcetegory__category'
    ).filter(
        id__in=unique_variant_ids
    )
    category_id = request.GET.get('category')
    q = (request.GET.get('q') or '').strip()

    qs = base_qs
    if category_id:
        qs = qs.filter(product__brand__subcetegory__category_id=category_id)
    if q:
        qs = qs.filter(
            Q(product__name__icontains=q) |
            Q(product__brand__name__icontains=q)
        )

    sales_sub = Subquery(
        OrderItem.objects.filter(variant_id=OuterRef('pk'))
        .values('variant_id')
        .annotate(s=Sum('quantity'))
        .values('s')[:1]
    )
    qs = qs.annotate(sales=sales_sub).order_by('-id')

    top_sellers = OrderItem.objects.values('variant_id').annotate(s=Sum('quantity')).order_by('-s')[:12]
    best_ids = {row['variant_id'] for row in top_sellers}

    buyer_id = request.session.get('buyer_id')
    wishlist_ids = set()
    if buyer_id:
        wishlist_ids = set(WishlistItem.objects.filter(buyer_id=buyer_id).values_list('variant_id', flat=True))

    paginator = Paginator(qs, 9)
    page = int(request.GET.get('page', 1) or 1)
    page_obj = paginator.get_page(page)

    items = []
    for v in page_obj:
        p = v.product
        img = _resolve_shop_image_url(p, v)
        
        # Get all available sizes for this product
        available_sizes = list(
            ProductVariant.objects.filter(
                product=p, 
                stock__gt=0
            ).values_list('size__name', flat=True).distinct().order_by('size__name')
        )
        
        items.append({
            "id": v.id,
            "price": float(v.price),
            "product_name": p.name,
            "brand_name": getattr(p.brand, 'name', ''),
            "image_url": img,
            "is_best": v.id in best_ids,
            "in_wishlist": v.id in wishlist_ids,
            "available_sizes": available_sizes,
        })
    return JsonResponse({
        "items": items,
        "meta": {
            "total": qs.count(),
            "start": page_obj.start_index() if items else 0,
            "end": page_obj.end_index() if items else 0,
            "page": page_obj.number,
            "pages": paginator.num_pages,
            "has_next": page_obj.has_next(),
            "has_prev": page_obj.has_previous(),
        }
    })

@never_cache
def toggle_wishlist_api(request, variant_id):
    buyer_id = request.session.get("buyer_id")
    if not buyer_id:
        return JsonResponse({"status": "error", "message": "Login required"}, status=401)
    
    try:
        buyer = Buyer.objects.get(id=buyer_id)
        variant = ProductVariant.objects.get(id=variant_id, product__status=True)
        
        wish_item = WishlistItem.objects.filter(buyer=buyer, variant=variant).first()
        if wish_item:
            wish_item.delete()
            return JsonResponse({"status": "removed", "in_wishlist": False})
        else:
            WishlistItem.objects.create(buyer=buyer, variant=variant)
            return JsonResponse({"status": "added", "in_wishlist": True})
            
    except (Buyer.DoesNotExist, ProductVariant.DoesNotExist):
        return JsonResponse({"status": "error", "message": "Not found"}, status=404)

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
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"status": "success", "message": "Added to cart", "cart_count": CartItem.objects.filter(buyer=buyer).count()})

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
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"status": "success", "message": "Added to wishlist"})
    return redirect("by_wishlist")

@never_cache
@buyer_login_required
def by_wishlist(request):
    buyer_id = request.session.get("buyer_id")
    buyer = Buyer.objects.get(id=buyer_id)
    items = WishlistItem.objects.select_related(
        "variant",
        "variant__product",
        "variant__product__brand"
    ).filter(buyer=buyer).order_by("-added_at")
    return render(request, "by_wishlist.html", {
        "wishlist_items": items
    })

@never_cache
@buyer_login_required
def remove_wishlist_item(request, item_id):
    buyer_id = request.session.get("buyer_id")
    if request.method == "POST":
        WishlistItem.objects.filter(id=item_id, buyer_id=buyer_id).delete()
    return redirect("by_wishlist")

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
        "variant__product",
        "variant__color",
        "variant__size"
    ).filter(buyer=buyer)

    subtotal = 0
    for item in cart_items:
        if item.quantity < 1:
            item.quantity = 1
            item.save()
        item.total_price = item.variant.price * item.quantity
        subtotal += item.total_price
        # Prioritize variant-specific image, then product image
        if item.variant.image and hasattr(item.variant.image, 'url'):
            item.image_url = item.variant.image.url
        elif item.variant.product.image and hasattr(item.variant.product.image, 'url'):
            item.image_url = item.variant.product.image.url
        else:
            item.image_url = None

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
        # Resolve image URL for each item
        item.image_url = _resolve_shop_image_url(item.variant.product, item.variant)
    
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
            
            # If payment method is UPI, create Razorpay order
            if payment_method == "upi":
                try:
                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    data = {
                        "amount": int(total * 100),  # amount in paise
                        "currency": "INR",
                        "receipt": order.order_number,
                    }
                    razorpay_order = client.order.create(data=data)
                    order.razorpay_order_id = razorpay_order['id']
                    order.save()
                    
                    return JsonResponse({
                        "success": True,
                        "payment_method": "upi",
                        "razorpay_order_id": razorpay_order['id'],
                        "razorpay_key": settings.RAZORPAY_KEY_ID,
                        "amount": float(total),
                        "order_id": order.id,
                        "currency": "INR",
                        "name": f"{first_name} {last_name}",
                        "email": email,
                        "phone": phone
                    })
                except Exception as e:
                    # This will trigger the rollback for the whole atomic transaction
                    raise ValueError(f"Razorpay order creation failed: {str(e)}")

            layer = get_channel_layer()
            if layer:
                payload = {
                    "id": order.id,
                    "order_number": order.order_number,
                    "buyer_id": buyer.id,
                    "buyer_name": buyer.name,
                    "email": order.email,
                    "total": float(order.total),
                    "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
                    "status": order.status,
                    "total_items": sum(i.quantity for i in order.items.all()),
                }   
                async_to_sync(layer.group_send)("orders", {
                    "type": "order_added",
                    "order": payload,
                })
    except Exception as e:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": str(e)})
        return redirect("by_checkout")
    
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "payment_method": "cash_on_delivery"})
    
    return redirect("by_thankyou")

@never_cache
@buyer_login_required
def verify_payment(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)
    
    import json
    try:
        data = json.loads(request.body)
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        order_id = data.get('orderId')
        
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        # Verify the signature
        client.utility.verify_payment_signature(params_dict)
        
        # If verification is successful, update the order
        order = Order.objects.get(id=order_id)
        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_signature = razorpay_signature
        order.payment_status = 'paid'
        order.save()
        
        # Notify admin via channels
        layer = get_channel_layer()
        if layer:
            payload = {
                "id": order.id,
                "order_number": order.order_number,
                "buyer_id": order.buyer_id,
                "buyer_name": order.buyer.name,
                "email": order.email,
                "total": float(order.total),
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
                "status": order.status,
                "total_items": sum(i.quantity for i in order.items.all()),
            }
            async_to_sync(layer.group_send)("orders", {
                "type": "order_added",
                "order": payload,
            })
            
        return JsonResponse({"success": True})
        
    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({"success": False, "error": "Invalid signature"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

@never_cache
@buyer_login_required
def cancel_unpaid_order(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)
    
    import json
    try:
        data = json.loads(request.body)
        order_id = data.get('orderId')
        order = Order.objects.get(id=order_id, payment_status='pending')
        
        # Return items to stock
        for item in order.items.all():
            ProductVariant.objects.filter(id=item.variant_id).update(stock=F('stock') + item.quantity)
        
        order.status = 'cancelled'
        order.save()
        
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

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
    
    for order in orders:
        for it in order.items.all():
            if it.variant:
                it.image_url = _resolve_shop_image_url(it.variant.product, it.variant)
            else:
                it.image_url = None

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
    layer = get_channel_layer()
    if layer:
        payload = {
            "id": order.id,
            "order_number": order.order_number,
            "buyer_id": order.buyer_id,
            "buyer_name": order.buyer.name,
            "email": order.email,
            "total": float(order.total),
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
            "status": order.status,
            "total_items": sum(i.quantity for i in order.items.all()),
        }
        async_to_sync(layer.group_send)("orders", {
            "type": "order_updated",
            "order": payload,
        })
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
    layer = get_channel_layer()
    if layer:
        payload = {
            "id": order.id,
            "order_number": order.order_number,
            "buyer_id": order.buyer_id,
            "buyer_name": order.buyer.name,
            "email": order.email,
            "total": float(order.total),
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
            "status": order.status,
            "total_items": sum(i.quantity for i in order.items.all()),
        }
        async_to_sync(layer.group_send)("orders", {
            "type": "order_updated",
            "order": payload,
        })
    messages.success(request, "Return request submitted. Supplier will verify shortly.")
    return redirect("by_history")

@never_cache
@buyer_login_required
def by_order_items_api(request, order_id):
    buyer_id = request.session.get("buyer_id")
    try:
        order = Order.objects.select_related("buyer").prefetch_related(
            "items",
            "items__variant",
            "items__variant__product",
            "items__variant__color",
            "items__variant__size",
        ).get(id=order_id, buyer_id=buyer_id)
    except Order.DoesNotExist:
        return JsonResponse({"items": []})
    items = []
    for it in order.items.all():
        img = getattr(getattr(it.variant.product, "image", None), "url", None)
        items.append({
            "product_name": it.product_name,
            "quantity": it.quantity,
            "price": float(it.price),
            "total": float(it.total),
            "image_url": img,
            "color": getattr(getattr(it.variant, "color", None), "name", ""),
            "size": getattr(getattr(it.variant, "size", None), "name", ""),
        })
    return JsonResponse({"items": items})

def by_logout(request):
    request.session.pop("buyer_id", None)
    request.session.pop("buyer_name", None)
    request.session.pop("buyer_email", None)
    messages.success(request, "Logged out successfully.", extra_tags="buyer")
    return redirect('by_index')

@never_cache
@buyer_login_required
def by_profile(request):
    buyer_id = request.session.get("buyer_id")
    try:
        buyer = Buyer.objects.get(id=buyer_id)
    except Buyer.DoesNotExist:
        return redirect("by_login")
    return render(request, "by_profile.html", {"buyer": buyer})

@never_cache
@buyer_login_required
def by_update_profile(request):
    if request.method != "POST":
        return redirect("by_profile")
    buyer_id = request.session.get("buyer_id")
    try:
        buyer = Buyer.objects.get(id=buyer_id)
    except Buyer.DoesNotExist:
        return redirect("by_login")
    
    # name and email are not changable
    gender = request.POST.get("gender", "").strip()
    phone = request.POST.get("phone", "").strip()
    address = request.POST.get("address", "").strip()
    city = request.POST.get("city", "").strip()
    state = request.POST.get("state", "").strip()
    pincode = request.POST.get("pincode", "").strip()
    profile_image = request.FILES.get("profile_image")
    
    if gender:
        buyer.gender = gender
    if phone:
        buyer.phone = phone
    if address:
        buyer.address = address
    if city:
        buyer.city = city
    if state:
        buyer.state = state
    if pincode:
        buyer.pincode = pincode
    if profile_image:
        buyer.profile_image = profile_image
        
    buyer.save()
    messages.success(request, "Profile updated successfully.", extra_tags="buyer")
    return redirect("by_profile")

@never_cache
@buyer_login_required
def by_order_receipt(request, order_id):
    buyer_id = request.session.get("buyer_id")
    try:
        order = Order.objects.select_related("buyer").prefetch_related(
            "items",
            "items__variant",
            "items__variant__product",
            "items__variant__color",
            "items__variant__size",
        ).get(id=order_id, buyer_id=buyer_id)
    except Order.DoesNotExist:
        return redirect("by_history")
    
    return render(request, "by_receipt.html", {"order": order})

