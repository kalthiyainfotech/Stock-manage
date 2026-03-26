from django.shortcuts import render , redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse
from .models import *
from buyers.models import Buyer, Order
from decimal import Decimal
import calendar
from datetime import date
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def auth_login(request):
    if request.user.is_authenticated:
        return redirect('auth_dashboard')

    if request.method == "POST":
        username = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('auth_dashboard')
        else:
            messages.error(request, "Invalid credentials", extra_tags="admin")

    return render(request, 'auth_login.html')

@never_cache
@login_required(login_url='auth_login')
def auth_logout(request):
    try:
        request.session.pop('_auth_user_id', None)
        request.session.pop('_auth_user_backend', None)
        request.session.pop('_auth_user_hash', None)
    finally:
        return redirect('auth_login')

@never_cache
@login_required(login_url='auth_login')
def auth_dashboard(request):
    stats = {
        'suppliers_count': Suppliers.objects.count(),
        'workers_count': Workers.objects.count(),
        'buyers_count': Buyer.objects.count(),
        'inventory_count': ProductVariant.objects.count(),
        'orders_count': Order.objects.count(),
        'contacts_count': Contact.objects.count(),
    }

    recent_orders = Order.objects.select_related('buyer').order_by('-created_at')[:5]
    recent_contacts = Contact.objects.order_by('-created_at')[:5]

    return render(request, 'auth_dashboard.html', {
        **stats,
        'recent_orders': recent_orders,
        'recent_contacts': recent_contacts,
    })

@never_cache
@login_required(login_url='auth_login')
def auth_suppliers(request):
    supplier_list = Suppliers.objects.all().order_by('-id')

    total_suppliers = supplier_list.count()
    active_suppliers = supplier_list.filter(status='Active').count()
    inactive_suppliers = supplier_list.filter(status='Inactive').count()

    paginator = Paginator(supplier_list, 10)  
    page_number = request.GET.get('page')
    suppliers = paginator.get_page(page_number)

    return render(request, 'auth_suppliers.html', {
        'suppliers': suppliers,
        'total_suppliers': total_suppliers,
        'active_suppliers': active_suppliers,
        'inactive_suppliers': inactive_suppliers,
    })

@never_cache
@login_required(login_url='auth_login')
def add_supplier(request):
    if request.method == "POST":
        s = Suppliers.objects.create(
            name=request.POST['name'],
            email=request.POST['email'],
            password=request.POST['password'],
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            state=request.POST.get('state'),
            city=request.POST.get('city'),
            address=request.POST.get('address'),
            mbno=request.POST['mbno'],
            gender=request.POST['gender'],
            status=request.POST['status'],
            profile_picture=request.FILES.get('profile_picture'),
            document=request.FILES.get('document'),
        )
        layer = get_channel_layer()
        if layer:
            async_to_sync(layer.group_send)("suppliers", {
                "type": "supplier_added",
                "supplier": {
                    "id": s.id,
                    "name": s.name,
                    "email": s.email,
                    "first_name": s.first_name,
                    "last_name": s.last_name,
                    "mbno": s.mbno,
                    "status": s.status,
                    "profile_picture": s.profile_picture.url if s.profile_picture else None,
                }
            })
        return redirect('auth_suppliers')

    return redirect('auth_suppliers')

@never_cache
@login_required(login_url='auth_login')
def edit_supplier(request, id):
    supplier = Suppliers.objects.get(id=id)

    if request.method == "POST":
        supplier.name = request.POST['name']
        supplier.email = request.POST['email']
        supplier.first_name = request.POST['first_name']
        supplier.last_name = request.POST['last_name']
        supplier.mbno = request.POST['mbno']
        supplier.state = request.POST.get('state')
        supplier.city = request.POST.get('city')
        supplier.address = request.POST.get('address')
        supplier.gender = request.POST['gender']
        supplier.status = request.POST['status']

        if request.FILES.get('profile_picture'):
            supplier.profile_picture = request.FILES['profile_picture']

        if request.FILES.get('document'):
            supplier.document = request.FILES['document']

        supplier.save()
        layer = get_channel_layer()
        if layer:
            async_to_sync(layer.group_send)("suppliers", {
                "type": "supplier_updated",
                "supplier": {
                    "id": supplier.id,
                    "name": supplier.name,
                    "email": supplier.email,
                    "first_name": supplier.first_name,
                    "last_name": supplier.last_name,
                    "mbno": supplier.mbno,
                    "status": supplier.status,
                    "profile_picture": supplier.profile_picture.url if supplier.profile_picture else None,
                }
            })

    return redirect('auth_suppliers')

@never_cache
@login_required(login_url='auth_login')
def delete_supplier(request, id):
    Suppliers.objects.filter(id=id).delete()
    layer = get_channel_layer()
    if layer:
        async_to_sync(layer.group_send)("suppliers", {
            "type": "supplier_deleted",
            "id": id,
        })
    return redirect('auth_suppliers')

@never_cache
@login_required(login_url='auth_login')
def auth_workers(request):
    worker_list = Workers.objects.all().order_by('-id')

    paginator = Paginator(worker_list, 10)  
    page_number = request.GET.get('page')
    workers = paginator.get_page(page_number)
    return render(request,'auth_workers.html',{
        'workers': workers
    })

@never_cache
@login_required(login_url='auth_login')
def add_worker(request):
    if request.method == "POST":
        Workers.objects.create(
            name=request.POST['name'],
            email=request.POST['email'],
            password=request.POST['password'],
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            state=request.POST.get('state'),
            city=request.POST.get('city'),
            address=request.POST.get('address'),
            mbno=request.POST['mbno'],
            salary=request.POST.get('salary') or 0,
            gender=request.POST['gender'],
            status=request.POST['status'],
            profile_picture=request.FILES.get('profile_picture'),
            document=request.FILES.get('document'),
        )
        return redirect('auth_workers')

    return redirect('auth_workers') 

@never_cache
@login_required(login_url='auth_login')
def edit_worker(request, id):
    worker = Workers.objects.get(id=id)

    if request.method == "POST":
        worker.name = request.POST['name']
        worker.email = request.POST['email']
        worker.first_name = request.POST['first_name']
        worker.last_name = request.POST['last_name']
        worker.mbno = request.POST['mbno']
        worker.salary = request.POST.get('salary') or worker.salary
        worker.state = request.POST.get('state')
        worker.city = request.POST.get('city')
        worker.address = request.POST.get('address')
        worker.gender = request.POST['gender']
        worker.status = request.POST['status']

        if request.FILES.get('profile_picture'):
            worker.profile_picture = request.FILES['profile_picture']

        if request.FILES.get('document'):
            worker.document = request.FILES['document']

        worker.save()

    return redirect('auth_workers')

@never_cache
@login_required(login_url='auth_login')
def delete_worker(request, id):
    Workers.objects.filter(id=id).delete()
    return redirect('auth_workers')

@never_cache
@login_required(login_url='auth_login')
def auth_holiday(request):
    holiday_list = Holiday.objects.all()
    paginator = Paginator(holiday_list, 10)
    page_number = request.GET.get('page')
    holidays = paginator.get_page(page_number)
    return render(request, 'auth_holiday.html', {
        'holidays': holidays
    })

@never_cache
@login_required(login_url='auth_login')
def add_holiday(request):
    if request.method == "POST":
        h = Holiday.objects.create(
            name=request.POST['name'],
            date=request.POST['date'],
            description=request.POST.get('description', '')
        )
        layer = get_channel_layer()
        if layer:
            payload = {
                "id": h.id,
                "name": h.name,
                "date": getattr(h.date, "isoformat", lambda: str(h.date))(),
                "description": h.description or "",
            }
            async_to_sync(layer.group_send)("holidays", {
                "type": "holiday_added",
                "holiday": payload,
            })
        return redirect('auth_holiday')
    return redirect('auth_holiday')

@never_cache
@login_required(login_url='auth_login')
def edit_holiday(request, id):
    holiday = get_object_or_404(Holiday, id=id)
    if request.method == "POST":
        holiday.name = request.POST['name']
        holiday.date = request.POST['date']
        holiday.description = request.POST.get('description', '')
        holiday.save()
        layer = get_channel_layer()
        if layer:
            payload = {
                "id": holiday.id,
                "name": holiday.name,
                "date": getattr(holiday.date, "isoformat", lambda: str(holiday.date))(),
                "description": holiday.description or "",
            }
            async_to_sync(layer.group_send)("holidays", {
                "type": "holiday_updated",
                "holiday": payload,
            })
    return redirect('auth_holiday')

@never_cache
@login_required(login_url='auth_login')
def delete_holiday(request, id):
    obj = get_object_or_404(Holiday, id=id)
    obj_id = obj.id
    obj_date = getattr(obj.date, "isoformat", lambda: str(obj.date))()
    obj.delete()
    layer = get_channel_layer()
    if layer:
        async_to_sync(layer.group_send)("holidays", {
            "type": "holiday_deleted",
            "id": obj_id,
            "date": obj_date,
        })
    return redirect('auth_holiday')

@never_cache
@login_required(login_url='auth_login')
def auth_leaves(request):
    leave_list = Leave.objects.select_related('worker').order_by('-created_at')
    paginator = Paginator(leave_list, 10)
    page_number = request.GET.get('page')
    leaves = paginator.get_page(page_number)
    stats = {
        'total': leave_list.count(),
        'pending': leave_list.filter(status='Pending').count(),
        'approved': leave_list.filter(status='Approved').count(),
        'rejected': leave_list.filter(status='Rejected').count(),
    }
    return render(request, 'auth_leaves.html', {
        'leaves': leaves,
        **stats,
    })

@never_cache
@login_required(login_url='auth_login')
def auth_work_salary(request):
    month_str = request.GET.get('month')
    today = date.today()
    if month_str:
        try:
            year, month = map(int, month_str.split('-'))
        except ValueError:
            year, month = today.year, today.month
    else:
        year, month = today.year, today.month
    days_in_month = calendar.monthrange(year, month)[1]
    month_start = date(year, month, 1)
    month_end = date(year, month, days_in_month)
    workers = Workers.objects.all().order_by('name')
    data = []
    for w in workers:
        qs = Leave.objects.filter(worker=w, status='Approved', start_date__lte=month_end, end_date__gte=month_start)
        total_leave_days = 0
        for lv in qs:
            s = lv.start_date if lv.start_date > month_start else month_start
            e = lv.end_date if lv.end_date < month_end else month_end
            if e >= s:
                total_leave_days += (e - s).days + 1
        unpaid_leaves = max(0, total_leave_days - 2)
        per_day = Decimal(w.salary) / Decimal(days_in_month) if days_in_month else Decimal('0')
        deduction = per_day * Decimal(unpaid_leaves)
        net_salary = Decimal(w.salary) - deduction
        data.append({
            'worker': w,
            'base_salary': w.salary,
            'days_in_month': days_in_month,
            'approved_leaves': total_leave_days,
            'free_leaves': 2,
            'unpaid_leaves': unpaid_leaves,
            'per_day': per_day,
            'deduction': deduction,
            'net_salary': net_salary,
        })
    return render(request, 'auth_work_salary.html', {
        'month': f"{year:04d}-{month:02d}",
        'year': year,
        'month_num': month,
        'days_in_month': days_in_month,
        'rows': data,
    })

@never_cache
@login_required(login_url='auth_login')
def approve_leave(request, id):
    leave = get_object_or_404(Leave, id=id)
    leave.status = 'Approved'
    leave.save()
    layer = get_channel_layer()
    if layer:
        payload = {
            "id": leave.id,
            "worker_id": leave.worker.id,
            "worker_name": leave.worker.name,
            "start_date": getattr(leave.start_date, "isoformat", lambda: str(leave.start_date))(),
            "end_date": getattr(leave.end_date, "isoformat", lambda: str(leave.end_date))(),
            "start_time": (leave.start_time.strftime("%H:%M") if hasattr(leave.start_time, "strftime") else (leave.start_time if leave.start_time else None)),
            "end_time": (leave.end_time.strftime("%H:%M") if hasattr(leave.end_time, "strftime") else (leave.end_time if leave.end_time else None)),
            "category": leave.category,
            "reason": leave.reason or "",
            "status": leave.status,
            "total_minutes": leave.total_minutes,
        }
        async_to_sync(layer.group_send)("leaves", {
            "type": "leave_updated",
            "leave": payload,
        })
    return redirect('auth_leaves')

@never_cache
@login_required(login_url='auth_login')
def reject_leave(request, id):
    leave = get_object_or_404(Leave, id=id)
    leave.status = 'Rejected'
    leave.save()
    layer = get_channel_layer()
    if layer:
        payload = {
            "id": leave.id,
            "worker_id": leave.worker.id,
            "worker_name": leave.worker.name,
            "start_date": getattr(leave.start_date, "isoformat", lambda: str(leave.start_date))(),
            "end_date": getattr(leave.end_date, "isoformat", lambda: str(leave.end_date))(),
            "start_time": (leave.start_time.strftime("%H:%M") if hasattr(leave.start_time, "strftime") else (leave.start_time if leave.start_time else None)),
            "end_time": (leave.end_time.strftime("%H:%M") if hasattr(leave.end_time, "strftime") else (leave.end_time if leave.end_time else None)),
            "category": leave.category,
            "reason": leave.reason or "",
            "status": leave.status,
            "total_minutes": leave.total_minutes,
        }
        async_to_sync(layer.group_send)("leaves", {
            "type": "leave_updated",
            "leave": payload,
        })
    return redirect('auth_leaves')

@never_cache
@login_required(login_url='auth_login')
def edit_leave_admin(request, id):
    leave = get_object_or_404(Leave, id=id)
    if request.method == "POST":
        leave.start_date = request.POST.get('start_date') or leave.start_date
        leave.end_date = request.POST.get('end_date') or leave.end_date
        leave.start_time = request.POST.get('start_time') or leave.start_time
        leave.end_time = request.POST.get('end_time') or leave.end_time
        category = request.POST.get('category') or leave.category
        if category in ['Sick', 'Emergency', 'Casual']:
            leave.category = category
        leave.reason = request.POST.get('reason', leave.reason)
        status = request.POST.get('status')
        if status in ['Pending', 'Approved', 'Rejected']:
            leave.status = status
        leave.save()
        layer = get_channel_layer()
        if layer:
            payload = {
                "id": leave.id,
                "worker_id": leave.worker.id,
                "worker_name": leave.worker.name,
                "start_date": getattr(leave.start_date, "isoformat", lambda: str(leave.start_date))(),
                "end_date": getattr(leave.end_date, "isoformat", lambda: str(leave.end_date))(),
                "start_time": (leave.start_time.strftime("%H:%M") if hasattr(leave.start_time, "strftime") else (leave.start_time if leave.start_time else None)),
                "end_time": (leave.end_time.strftime("%H:%M") if hasattr(leave.end_time, "strftime") else (leave.end_time if leave.end_time else None)),
                "category": leave.category,
                "reason": leave.reason or "",
                "status": leave.status,
                "total_minutes": leave.total_minutes,
            }
            async_to_sync(layer.group_send)("leaves", {
                "type": "leave_updated",
                "leave": payload,
            })
    return redirect('auth_leaves')

@never_cache
@login_required(login_url='auth_login')
def delete_leave_admin(request, id):
    obj = Leave.objects.filter(id=id).first()
    if obj:
        obj_id = obj.id
        wid = obj.worker.id
        sd = getattr(obj.start_date, "isoformat", lambda: str(obj.start_date))()
        ed = getattr(obj.end_date, "isoformat", lambda: str(obj.end_date))()
        obj.delete()
        layer = get_channel_layer()
        if layer:
            async_to_sync(layer.group_send)("leaves", {
                "type": "leave_deleted",
                "id": obj_id,
                "worker_id": wid,
                "start_date": sd,
                "end_date": ed,
            })
    return redirect('auth_leaves')



@never_cache
@login_required(login_url='auth_login')
def add_inventory(request):
    if request.method == "POST":
        

        category_name = request.POST.get('new_category') or request.POST.get('category')
        if not category_name:
            messages.error(request, "Category is required")
            return redirect('auth_inventory')
        
        category, created_category = Category.objects.get_or_create(
            name=category_name
        )
        if created_category:
            layer = get_channel_layer()
            async_to_sync(layer.group_send)("categories", {
                "type": "category_added",
                "category": {"id": category.id, "name": category.name}
            })

        subcategory_name = request.POST.get('new_subcategory') or request.POST.get('subcategory')
        if not subcategory_name:
            messages.error(request, "Subcategory is required")
            return redirect('auth_inventory')
        
        subcategory, _ = Subcetegory.objects.get_or_create(
            category=category,
            name=subcategory_name
        )

        brand_name = request.POST.get('new_brand') or request.POST.get('brand')
        if not brand_name:
            messages.error(request, "Brand is required")
            return redirect('auth_inventory')
        
        brand, _ = Brand.objects.get_or_create(
            subcetegory=subcategory,
            name=brand_name
        )

        product_name = request.POST.get('new_product') or request.POST.get('product')
        if not product_name:
            messages.error(request, "Product is required")
            return redirect('auth_inventory')
        
        product, _ = Product.objects.get_or_create(
            brand=brand,
            name=product_name,
            defaults={
                'description': request.POST.get('description', ''),
                'base_price': request.POST.get('price') or 0,
            }
        )
        
        if not _:
            product.description = request.POST.get('description', '')
            product.base_price = request.POST.get('price') or 0
            product.save()

        indexes = request.POST.getlist('variant_index')
        colors = request.POST.getlist('variant_color')
        sizes = request.POST.getlist('variant_size')
        prices = request.POST.getlist('variant_price')
        stocks = request.POST.getlist('variant_stock')
        skus = request.POST.getlist('variant_sku')
        media_indexes = request.POST.getlist('variant_media_index')

        spec_names = request.POST.getlist('spec_name')
        spec_values = request.POST.getlist('spec_value')
        
        layer = get_channel_layer()

        if colors:
            color_variants = {}
            processed_media = {} # media_idx -> { 'main': image_file/None, 'gallery': [file_list] }
            
            # Map of media_idx to the first variant that "owns" the files
            # to avoid re-saving the same request.FILES object which creates duplicate files
            
            for i in range(len(colors)):
                idx = indexes[i] if i < len(indexes) else i
                media_idx = str(media_indexes[i] if i < len(media_indexes) and media_indexes[i] else idx)
                color_name = colors[i].strip().lower() or 'default'
                size_name = sizes[i].strip() if i < len(sizes) else 'Default'
                size_name = size_name or 'Default'
                price_val = prices[i] if i < len(prices) and prices[i] else 0
                stock_val = stocks[i] if i < len(stocks) and stocks[i] else 0
                input_sku = skus[i].strip() if i < len(skus) and skus[i] else ''

                color, _ = Color.objects.get_or_create(name=color_name)
                size, _ = Size.objects.get_or_create(name=size_name)
                sku = input_sku or f"{product.id}-{color.id}-{size.id}"

                variant, created = ProductVariant.objects.get_or_create(
                    product=product,
                    color=color,
                    size=size,
                    defaults={
                        'price': price_val,
                        'stock': stock_val,
                        'sku': sku
                    }
                )
                if not created:
                    variant.price = price_val
                    variant.stock = stock_val
                    variant.sku = sku
                    variant.save()

                # Process Media only once per media_idx
                if media_idx not in processed_media:
                    v_image = request.FILES.get(f'variant_image_{media_idx}')
                    v_galleries = request.FILES.getlist(f'variant_gallery_{media_idx}')
                    
                    # Store what we found for this group
                    processed_media[media_idx] = {
                        'main': v_image,
                        'gallery_files': v_galleries,
                        'primary_variant': variant 
                    }
                    
                    if v_image:
                        variant.image = v_image
                        variant.save()
                        if not product.image:
                            product.image = v_image
                            product.save()
                    
                    # Add gallery images only for the primary variant in this group
                    for gi in v_galleries:
                        if gi:
                            VariantImage.objects.create(variant=variant, image=gi)
                else:
                    # For subsequent variants in the same media group, point to the primary variant's files
                    primary_entry = processed_media[media_idx]
                    primary_variant = primary_entry['primary_variant']
                    
                    if primary_variant.image and not variant.image:
                        variant.image = primary_variant.image.name
                        variant.save()
                    
                    # We don't create new VariantImage records here because we want 
                    # the display logic to find them via the primary variant or 
                    # we will ensure they are linked. 
                    # Actually, for the "one per color" expected behavior, 
                    # it's better if they share the same physical file on disk.
                
                if color_name not in color_variants:
                    color_variants[color_name] = []
                color_variants[color_name].append(variant)

                VariantSpec.objects.filter(variant=variant).delete()
                for name, value in zip(spec_names, spec_values):
                    name = (name or '').strip()
                    value = (value or '').strip()
                    if name and value:
                        VariantSpec.objects.create(variant=variant, name=name, value=value)

                if layer:
                    payload = {
                        "id": variant.id,
                        "product_name": product.name,
                        "brand_name": brand.name,
                        "category_name": category.name,
                        "price": float(variant.price),
                        "stock": variant.stock,
                    }
                    async_to_sync(layer.group_send)("inventory", {
                        "type": "inventory_added",
                        "inventory": payload,
                    })

            # Cleanup / Final Pass for syncing colors if needed
            for c_key, variants_in_color in color_variants.items():
                source_v = next((v for v in variants_in_color if v.image), None)
                if source_v:
                    for target_v in variants_in_color:
                        if not target_v.image:
                            target_v.image = source_v.image.name
                            target_v.save()
                
                # Cross-link gallery images for consistency if some variants missed them
                # (though the media_idx logic usually handles this now)
                source_v_with_gallery = next((v for v in variants_in_color if v.gallery_images.exists()), None)
                if source_v_with_gallery:
                    source_gallery = list(source_v_with_gallery.gallery_images.all())
                    for target_v in variants_in_color:
                        if target_v != source_v_with_gallery and not target_v.gallery_images.exists():
                            for sg in source_gallery:
                                VariantImage.objects.create(variant=target_v, image=sg.image.name)
        else:
            # Fallback for single variant
            color_name = request.POST.get('color', '').strip() or 'Default'
            size_name = request.POST.get('size', '').strip() or 'Default'
            color, _ = Color.objects.get_or_create(name=color_name)
            size, _ = Size.objects.get_or_create(name=size_name)
            sku = f"{product.id}-{color.id}-{size.id}"
            variant, created = ProductVariant.objects.get_or_create(
                product=product,
                color=color,
                size=size,
                defaults={
                    'price': request.POST.get('price') or 0,
                    'stock': request.POST.get('stock') or 0,
                    'sku': sku
                }
            )
            if not created:
                variant.price = request.POST.get('price') or 0
                variant.stock = request.POST.get('stock') or 0
                variant.save()

            v_image = request.FILES.get('variant_image_0')
            if v_image:
                variant.image = v_image
                variant.save()
                # If product has no image, use the first variant's image as default
                if not product.image:
                    product.image = v_image
                    product.save()
            
            v_galleries = request.FILES.getlist('variant_gallery_0')
            for gi in v_galleries:
                if gi:
                    VariantImage.objects.create(variant=variant, image=gi)

            VariantSpec.objects.filter(variant=variant).delete()
            for name, value in zip(spec_names, spec_values):
                name = (name or '').strip()
                value = (value or '').strip()
                if name and value:
                    VariantSpec.objects.create(variant=variant, name=name, value=value)

            if layer:
                payload = {
                    "product_id": product.id,
                    "product_name": product.name,
                    "brand_name": brand.name,
                    "category_name": category.name,
                    "variant_id": variant.id,
                    "price": float(variant.price),
                    "stock": variant.stock,
                }
                async_to_sync(layer.group_send)("inventory", {
                    "type": "inventory_added",
                    "inventory": payload,
                })

        messages.success(request, "Inventory added successfully")
        return redirect('auth_inventory')

    return redirect('auth_inventory')

@never_cache
@login_required(login_url='auth_login')
def auth_inventory(request):
    # Paginate by Product instead of ProductVariant, and only show products with variants
    product_list = Product.objects.annotate(
        variant_count=Count('variants')
    ).filter(variant_count__gt=0).select_related(
        'brand',
        'brand__subcetegory',
        'brand__subcetegory__category'
    ).order_by('-id')

    paginator = Paginator(product_list, 10)
    page_number = request.GET.get('page')
    inventory_page = paginator.get_page(page_number)

    categories = Category.objects.filter(status=True).order_by('name')

    # Get all variants for the products on this page
    product_ids = [p.id for p in inventory_page]
    all_variants = ProductVariant.objects.filter(product_id__in=product_ids).select_related(
        'product',
        'color',
        'size',
        'product__brand',
        'product__brand__subcetegory',
        'product__brand__subcetegory__category'
    ).prefetch_related('gallery_images', 'specs').order_by('-id')

    groups = []
    for p in inventory_page:
        variants = [v for v in all_variants if v.product_id == p.id]
        if variants:
            # Calculate total stock across all variants for this product
            total_stock = sum(v.stock for v in variants)
            # Inject total_stock into the first variant so template doesn't need much change
            # We use a temporary attribute to avoid saving to DB if anyone calls .save()
            # but in this context it's safe since it's just for display.
            variants[0].stock = total_stock 
            
            groups.append({
                'product': p,
                'variants': variants,
            })

    return render(request, 'auth_inventory.html', {
        'inventorys': inventory_page,
        'inventory_groups': groups,
        'categories': categories
    })

@never_cache
@login_required(login_url='auth_login')
def edit_inventory(request, id):
    try:
        inventory = ProductVariant.objects.get(id=id)
    except ProductVariant.DoesNotExist:
        messages.error(request, "Inventory not found")
        return redirect('auth_inventory')

    if request.method == "POST":

        category_name = request.POST.get('new_category') or request.POST.get('category')
        if not category_name:
            messages.error(request, "Category is required")
            return redirect('auth_inventory')
        
        category, created_category = Category.objects.get_or_create(
            name=category_name
        )
        if created_category:
            layer = get_channel_layer()
            async_to_sync(layer.group_send)("categories", {
                "type": "category_added",
                "category": {"id": category.id, "name": category.name}
            })

        subcategory_name = request.POST.get('new_subcategory') or request.POST.get('subcategory')
        if not subcategory_name:
            messages.error(request, "Subcategory is required")
            return redirect('auth_inventory')
        
        subcategory, _ = Subcetegory.objects.get_or_create(
            category=category,
            name=subcategory_name
        )

        brand_name = request.POST.get('new_brand') or request.POST.get('brand')
        if not brand_name:
            messages.error(request, "Brand is required")
            return redirect('auth_inventory')
        
        brand, _ = Brand.objects.get_or_create(
            subcetegory=subcategory,
            name=brand_name
        )

        product_name = request.POST.get('new_product') or request.POST.get('product')
        if not product_name:
            messages.error(request, "Product is required")
            return redirect('auth_inventory')
        
        product = inventory.product
        product.brand = brand
        product.name = product_name
        product.description = request.POST.get('description', '')
        product.base_price = request.POST.get('price') or 0
        product.save()

        color_names = request.POST.getlist('variant_color')
        size_names = request.POST.getlist('variant_size')
        price_vals = request.POST.getlist('variant_price')
        stock_vals = request.POST.getlist('variant_stock')
        sku_vals = request.POST.getlist('variant_sku')
        media_indexes = request.POST.getlist('variant_media_index')

        # Map to prevent duplicate image processing for variants sharing the same media index
        processed_media = {}

        if color_names:
            # Using basic dicts with list values for safest type inference
            c_groups = {} 
            c_m_indices = {}
            
            for i in range(len(color_names)):
                m_idx_val = str(media_indexes[i] if i < len(media_indexes) else i)
                color_name = (color_names[i] or '').strip().lower() or 'default'
                size_name = (size_names[i] or '').strip() if i < len(size_names) else 'Default'
                price_val = price_vals[i] if (i < len(price_vals) and price_vals[i]) else 0
                stock_val = stock_vals[i] if (i < len(stock_vals) and stock_vals[i]) else 0
                sku_val = sku_vals[i].strip() if (i < len(sku_vals) and sku_vals[i]) else f"{product.id}-{i}"
                
                clr_obj, _ = Color.objects.get_or_create(name=color_name)
                sz_obj, _ = Size.objects.get_or_create(name=size_name)
                
                if i == 0:
                    v = inventory
                    v.color = clr_obj
                    v.size = sz_obj
                else:
                    v, _ = ProductVariant.objects.get_or_create(
                        product=product,
                        color=clr_obj,
                        size=sz_obj,
                        defaults={'price': price_val, 'stock': stock_val, 'sku': sku_val}
                    )
                
                v.price = price_val
                v.stock = stock_val
                v.sku = sku_val
                v.save()
                
                if color_name not in c_groups:
                    c_groups[color_name] = []
                if color_name not in c_m_indices:
                    c_m_indices[color_name] = []
                
                c_groups[color_name].append(v)
                if m_idx_val not in c_m_indices[color_name]:
                    c_m_indices[color_name].append(m_idx_val)
                
                # Update Specs
                VariantSpec.objects.filter(variant=v).delete()
                spec_names = request.POST.getlist('spec_name')
                spec_values = request.POST.getlist('spec_value')
                for sn, sv in zip(spec_names, spec_values):
                    sn_str = (sn or '').strip()
                    sv_str = (sv or '').strip()
                    if sn_str and sv_str:
                        VariantSpec.objects.create(variant=v, name=sn_str, value=sv_str)
            
            # Phase 2: Synchronize Images by Color Group
            for c_key in c_groups:
                members = c_groups[c_key]
                primary_v = members[0]
                idx_list = c_m_indices.get(c_key, [])
                
                for m_idx in idx_list:
                    # Combined Main Deletions
                    if request.POST.get(f'delete_variant_main_{m_idx}') == 'true' and primary_v.image:
                        primary_v.image = None
                        primary_v.save()
                    
                    # Combined Gallery Deletions
                    gal_delete_urls = request.POST.getlist(f'delete_variant_gallery_{m_idx}')
                    for gd_url in gal_delete_urls:
                        if gd_url:
                            filename = gd_url.split('/')[-1]
                            VariantImage.objects.filter(variant=primary_v, image__icontains=filename).delete()
                            ProductImage.objects.filter(product=product, image__icontains=filename).delete()

                # 2. Combined Uploads for the group
                for m_idx in idx_list:
                    new_main_file = request.FILES.get(f'variant_image_{m_idx}')
                    if new_main_file:
                        primary_v.image = new_main_file
                        primary_v.save()
                        if not product.image:
                            product.image = new_main_file
                            product.save()
                    
                    new_gallery_files = request.FILES.getlist(f'variant_gallery_{m_idx}')
                    for ngf in new_gallery_files:
                        if ngf:
                            VariantImage.objects.create(variant=primary_v, image=ngf)

                # 3. Propagate images to EVERY variant of this color in the database
                all_color_variants = ProductVariant.objects.filter(product=product, color=primary_v.color)
                for mirror_v in all_color_variants:
                    if mirror_v.id == primary_v.id:
                        continue
                    
                    # Update main image
                    mirror_v.image = primary_v.image
                    mirror_v.save()
                    
                    # Synchronize gallery by mirroring VariantImage records
                    VariantImage.objects.filter(variant=mirror_v).delete()
                    for v_img_obj in VariantImage.objects.filter(variant=primary_v):
                        VariantImage.objects.create(variant=mirror_v, image=v_img_obj.image)

            # Phase 3: Real-time Updates (Notify about all variants of this product)
            layer = get_channel_layer()
            if layer:
                for v in ProductVariant.objects.filter(product=product):
                    gv_urls = [vi.image.url for vi in v.gallery_images.all() if vi.image]
                    v_payload = {
                        "id": v.id,
                        "product_id": product.id,
                        "product_name": product.name,
                        "color_id": v.color.id,
                        "color_name": v.color.name,
                        "size_id": v.size.id,
                        "price": float(v.price),
                        "stock": v.stock,
                        "image_url": v.image.url if v.image else None,
                        "gallery_urls": gv_urls,
                    }
                    async_to_sync(layer.group_send)("inventory", {
                        "type": "inventory_updated",
                        "inventory": v_payload,
                    })

        messages.success(request, "Inventory updated successfully")
        return redirect('auth_inventory')

    return redirect('auth_inventory')

@never_cache
@login_required(login_url='auth_login')
def delete_inventory(request, id):
    inventory = ProductVariant.objects.get(id=id)
    inv_id = inventory.id
    inventory.delete()

    layer = get_channel_layer()
    if layer:
        async_to_sync(layer.group_send)("inventory", {
            "type": "inventory_deleted",
            "id": inv_id,
        })

    return redirect('auth_inventory')

@never_cache
@login_required(login_url='auth_login')
def delete_product_inventory(request, product_id):
    """Deletes all variants of a product."""
    variants = ProductVariant.objects.filter(product_id=product_id)
    ids = list(variants.values_list('id', flat=True))
    variants.delete()
    
    layer = get_channel_layer()
    if layer:
        for vid in ids:
            async_to_sync(layer.group_send)("inventory", {
                "type": "inventory_deleted",
                "id": vid,
            })
            
    messages.success(request, f"Deleted all variants for product ID {product_id}")
    return redirect('auth_inventory')

@never_cache
@login_required(login_url='auth_login')
def get_subcategories(request):
    category_name = request.GET.get('category_name')
    if category_name:
        try:
            category = Category.objects.get(name=category_name, status=True)
            subcategories = Subcetegory.objects.filter(
                category=category, 
                status=True
            ).order_by('name')
            data = [{'id': sub.id, 'name': sub.name} for sub in subcategories]
            return JsonResponse(data, safe=False)
        except Category.DoesNotExist:
            return JsonResponse([], safe=False)
    return JsonResponse([], safe=False)

@never_cache
@login_required(login_url='auth_login')
def get_brands(request):
    subcategory_name = request.GET.get('subcategory_name')
    category_name = request.GET.get('category_name')
    if subcategory_name and category_name:
        try:
            category = Category.objects.get(name=category_name, status=True)
            subcategory = Subcetegory.objects.get(
                category=category,
                name=subcategory_name, 
                status=True
            )
            brands = Brand.objects.filter(
                subcetegory=subcategory, 
                status=True
            ).order_by('name')
            data = [{'id': brand.id, 'name': brand.name} for brand in brands]
            return JsonResponse(data, safe=False)
        except (Category.DoesNotExist, Subcetegory.DoesNotExist):
            return JsonResponse([], safe=False)
    return JsonResponse([], safe=False)

@never_cache
@login_required(login_url='auth_login')
def get_products(request):
    brand_name = request.GET.get('brand_name')
    subcategory_name = request.GET.get('subcategory_name')
    category_name = request.GET.get('category_name')
    if brand_name and subcategory_name and category_name:
        try:
            category = Category.objects.get(name=category_name, status=True)
            subcategory = Subcetegory.objects.get(
                category=category,
                name=subcategory_name, 
                status=True
            )
            brand = Brand.objects.get(
                subcetegory=subcategory,
                name=brand_name, 
                status=True
            )
            products = Product.objects.filter(
                brand=brand, 
                status=True
            ).order_by('name')
            data = [{'id': prod.id, 'name': prod.name} for prod in products]
            return JsonResponse(data, safe=False)
        except (Category.DoesNotExist, Subcetegory.DoesNotExist, Brand.DoesNotExist):
            return JsonResponse([], safe=False)
    return JsonResponse([], safe=False)

@never_cache
@login_required(login_url='auth_login')
def auth_buyers(request):
    buyers = Buyer.objects.all().order_by('-id') 
    context = {
        'buyers': buyers
    }
    return render(request, 'auth_buyers.html', context)

@never_cache
@login_required(login_url='auth_login')
def delete_buyer(request, id):
    buyer = Buyer.objects.get(id=id)
    buyer.delete()
    return redirect('auth_buyers')

@never_cache
@login_required(login_url='auth_login')
def auth_blogs(request):
    blogs_list = Blogs.objects.all().order_by('-id')

    paginator = Paginator(blogs_list, 10)
    page_number = request.GET.get('page')
    blogs = paginator.get_page(page_number)

    return render(request, 'auth_blogs.html', {
        'blogs': blogs
    })

@never_cache
@login_required(login_url='auth_login')
def add_blogs(request):
    if request.method == "POST":
        blog = Blogs.objects.create(
            image=request.FILES.get('image'),
            des=request.POST.get('des'),
            by=request.POST.get('by'),
            date=request.POST.get('date'), 
        )
        layer = get_channel_layer()
        if layer:
            data = {
                "id": blog.id,
                "des": blog.des,
                "by": blog.by,
                "date": str(blog.date),
                "image_url": blog.image.url if blog.image else None,
            }
            async_to_sync(layer.group_send)("blogs", {"type": "blog_added", "blog": data})
    return redirect('auth_blogs')

@never_cache
@login_required(login_url='auth_login')
def edit_blogs(request, id):
    blog = get_object_or_404(Blogs, id=id)

    if request.method == "POST":
        blog.des = request.POST.get('des')
        blog.by = request.POST.get('by')
        blog.date = request.POST.get('date')

        if request.FILES.get('image'):
            blog.image = request.FILES.get('image')

        blog.save()
        layer = get_channel_layer()
        if layer:
            data = {
                "id": blog.id,
                "des": blog.des,
                "by": blog.by,
                "date": str(blog.date),
                "image_url": blog.image.url if blog.image else None,
            }
            async_to_sync(layer.group_send)("blogs", {"type": "blog_updated", "blog": data})

    return redirect('auth_blogs')

@never_cache
@login_required(login_url='auth_login')
def delete_blogs(request, id):
    b = Blogs.objects.filter(id=id).first()
    bid = b.id if b else id
    Blogs.objects.filter(id=id).delete()
    layer = get_channel_layer()
    if layer:
        async_to_sync(layer.group_send)("blogs", {"type": "blog_deleted", "id": bid})
    return redirect('auth_blogs')

@never_cache
@login_required(login_url='auth_login')
def auth_contacts(request):
    contacts_list = Contact.objects.all().order_by('-id')

    paginator = Paginator(contacts_list, 10)
    page_number = request.GET.get('page')
    contacts = Paginator(contacts_list, 10).get_page(page_number)

    return render(request, 'auth_contacts.html', {
        'contacts': contacts
    })

@never_cache
@login_required(login_url='auth_login')
def delete_contact(request, id):
    Contact.objects.filter(id=id).delete()
    return redirect('auth_contacts')

@never_cache
@login_required(login_url='auth_login')
def auth_order(request):
    if request.method == "POST":
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        order = get_object_or_404(Order, id=order_id)
        order.status = new_status
        order.save()

        layer = get_channel_layer()
        if layer:
            order_data = {
                "order_id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "buyer_id": order.buyer.id,
            }
            async_to_sync(layer.group_send)(
                f"user_{order.buyer.id}",
                {
                    "type": "order_status_updated",
                    "order": order_data
                }
            )

        return JsonResponse({"status": "success", "new_status": new_status})

    orders_list = Order.objects.select_related('buyer').prefetch_related('items').all().order_by('-created_at')
    
    paginator = Paginator(orders_list, 10)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    return render(request, 'auth_orders.html', {
        'orders': orders
    })

@never_cache
@login_required(login_url='auth_login')
def delete_order(request, id):
    exists = Order.objects.filter(id=id).first()
    Order.objects.filter(id=id).delete()
    layer = get_channel_layer()
    if layer and exists:
        async_to_sync(layer.group_send)("orders", {
            "type": "order_deleted",
            "id": exists.id,
        })
    return redirect('auth_order')

@never_cache
@login_required(login_url='auth_login')
def admin_order_items_api(request, order_id):
    try:
        order = Order.objects.select_related("buyer").prefetch_related(
            "items",
            "items__variant",
            "items__variant__product",
            "items__variant__color",
            "items__variant__size",
        ).get(id=order_id)
    except Order.DoesNotExist:
        return JsonResponse({"items": []})
    items = []
    for it in order.items.all():
        img = getattr(getattr(it.variant.product, "image", None), "url", None) if getattr(it, "variant", None) and getattr(it.variant, "product", None) else None
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
