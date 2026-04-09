from django.shortcuts import render , redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import *
from buyers.models import Buyer, Order, OrderItem
from decimal import Decimal
import calendar
from datetime import date
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncMonth
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
    categories = Category.objects.all().order_by('name')
    subcategories = Subcetegory.objects.select_related('category').order_by('category__name', 'name')

    # Data for Charts
    # 1. Sales by Category
    category_sales_data = OrderItem.objects.filter(order__status='delivered').values(
        name=F('variant__product__brand__subcetegory__category__name')
    ).annotate(
        value=Sum('total')
    ).order_by('-value')

    # 2. Monthly Sales (Last 6 months)
    monthly_sales_data = Order.objects.filter(status='delivered').annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total_sales=Sum('total')
    ).order_by('month')

    # 3. Top Selling Products
    top_selling_products = OrderItem.objects.filter(order__status='delivered').values(
        'product_name'
    ).annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('total')
    ).order_by('-total_qty')[:5]

    import json
    from django.core.serializers.json import DjangoJSONEncoder

    context = {
        **stats,
        'recent_orders': recent_orders,
        'recent_contacts': recent_contacts,
        'categories': categories,
        'subcategories': subcategories,
        'category_sales_json': json.dumps(list(category_sales_data), cls=DjangoJSONEncoder),
        'monthly_sales_json': json.dumps([
            {'month': s['month'].strftime('%b %Y'), 'total_sales': float(s['total_sales'])} 
            for s in monthly_sales_data
        ], cls=DjangoJSONEncoder),
        'top_products_json': json.dumps(list(top_selling_products), cls=DjangoJSONEncoder),
    }

    return render(request, 'auth_dashboard.html', context)

@never_cache
@login_required(login_url='auth_login')
def delete_category(request, id):
    Category.objects.filter(id=id).delete()
    return redirect('auth_dashboard')

@never_cache
@login_required(login_url='auth_login')
def delete_subcategory(request, id):
    Subcetegory.objects.filter(id=id).delete()
    return redirect('auth_dashboard')

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
        email = request.POST.get('email', '').strip()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Check for duplicate email
        if Suppliers.objects.filter(email=email).exists():
            if is_ajax:
                return JsonResponse({'status': 'error', 'error': 'email_exists', 'message': 'A supplier with this email already exists.'}, status=400)
            return redirect('auth_suppliers')

        Suppliers.objects.create(
            name=request.POST['name'],
            email=email,
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
        if is_ajax:
            return JsonResponse({'status': 'success', 'message': 'Supplier added successfully'})
        return redirect('auth_suppliers')

    return redirect('auth_suppliers')


@never_cache
@login_required(login_url='auth_login')
def check_supplier_email(request):
    """API endpoint to check if a supplier email already exists."""
    email = request.GET.get('email', '').strip()
    supplier_id = request.GET.get('supplier_id', '')  # Exclude current supplier when editing
    qs = Suppliers.objects.filter(email=email)
    if supplier_id:
        qs = qs.exclude(id=supplier_id)
    return JsonResponse({'exists': qs.exists()})

@never_cache
@login_required(login_url='auth_login')
def edit_supplier(request, id):
    supplier = Suppliers.objects.get(id=id)

    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Check for duplicate email excluding this supplier
        if Suppliers.objects.filter(email=email).exclude(id=id).exists():
            if is_ajax:
                return JsonResponse({'status': 'error', 'error': 'email_exists', 'message': 'A supplier with this email already exists.'}, status=400)
            return redirect('auth_suppliers')

        supplier.name = request.POST['name']
        supplier.email = email
        supplier.first_name = request.POST['first_name']
        supplier.last_name = request.POST['last_name']
        supplier.mbno = request.POST['mbno']
        supplier.state = request.POST.get('state')
        supplier.city = request.POST.get('city')
        supplier.address = request.POST.get('address')
        supplier.gender = request.POST['gender']
        supplier.status = request.POST['status']

        password = request.POST.get('password')
        if password:
            supplier.password = password

        if request.POST.get('remove_profile_picture') == 'true':
            supplier.profile_picture = None

        if request.FILES.get('profile_picture'):
            supplier.profile_picture = request.FILES['profile_picture']

        if request.FILES.get('document'):
            supplier.document = request.FILES['document']

        supplier.save()

        if is_ajax:
            return JsonResponse({'status': 'success', 'message': 'Supplier updated successfully'})

    return redirect('auth_suppliers')

@never_cache
@login_required(login_url='auth_login')
def delete_supplier(request, id):
    Suppliers.objects.filter(id=id).delete()
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
        email = request.POST.get('email', '').strip()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if Workers.objects.filter(email=email).exists():
            if is_ajax:
                return JsonResponse({'status': 'error', 'error': 'email_exists', 'message': 'Email already exists.'}, status=400)
            return redirect('auth_workers')

        Workers.objects.create(
            email=email,
            password=request.POST.get('password', ''),
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''),
            state=request.POST.get('state'),
            city=request.POST.get('city'),
            address=request.POST.get('address'),
            mbno=request.POST.get('mbno', 0),
            salary=request.POST.get('salary') or 0,
            joining_date=request.POST.get('joining_date') or None,
            resignation_date=request.POST.get('resignation_date') or None,
            gender=request.POST.get('gender', 'Other'),
            status=request.POST.get('status', 'Active'),
            profile_picture=request.FILES.get('profile_picture'),
            document=request.FILES.get('document'),
        )
        if is_ajax:
            return JsonResponse({'status': 'success'})
        return redirect('auth_workers')

    return redirect('auth_workers') 

@never_cache
@login_required(login_url='auth_login')
def edit_worker(request, id):
    worker = Workers.objects.get(id=id)

    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if Workers.objects.filter(email=email).exclude(id=id).exists():
            if is_ajax:
                return JsonResponse({'status': 'error', 'error': 'email_exists', 'message': 'Email already exists.'}, status=400)
            return redirect('auth_workers')

        worker.email = email
        worker.first_name = request.POST.get('first_name', '')
        worker.last_name = request.POST.get('last_name', '')
        worker.mbno = request.POST.get('mbno', worker.mbno)
        worker.salary = request.POST.get('salary') or worker.salary
        worker.state = request.POST.get('state')
        worker.city = request.POST.get('city')
        worker.address = request.POST.get('address')
        worker.joining_date = request.POST.get('joining_date') or None
        worker.resignation_date = request.POST.get('resignation_date') or None
        worker.gender = request.POST.get('gender')
        worker.status = request.POST.get('status')

        if request.POST.get('remove_profile_picture') == 'true':
            worker.profile_picture = None

        if request.POST.get('remove_document') == 'true':
            worker.document = None

        if request.FILES.get('profile_picture'):
            worker.profile_picture = request.FILES['profile_picture']

        if request.FILES.get('document'):
            worker.document = request.FILES['document']

        worker.save()
        if is_ajax:
            return JsonResponse({'status': 'success'})
        return redirect('auth_workers')

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

    workers = Workers.objects.all().order_by('first_name')
    data = []
    import calendar
    for w in workers:
        res = w.calculate_salary_for_month(year, month)
        if res:
            data.append({
                'worker': w,
                **res
            })

    return render(request, 'auth_work_salary.html', {
        'month': f"{year:04d}-{month:02d}",
        'year': year,
        'month_num': month,
        'rows': data,
        'days_in_month': calendar.monthrange(year, month)[1]
    })

@never_cache
@login_required(login_url='auth_login')
def worker_salary_history(request, id):
    worker = get_object_or_404(Workers, id=id)
    history = worker.get_salary_history()
    return render(request, 'worker_salary_history.html', {
        'worker': worker,
        'history': history
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
            "worker_name": f"{leave.worker.first_name} {leave.worker.last_name}",
            "start_date": getattr(leave.start_date, "isoformat", lambda: str(leave.start_date))(),
            "end_date": getattr(leave.end_date, "isoformat", lambda: str(leave.end_date))(),
            "start_time": (leave.start_time.strftime("%H:%M") if hasattr(leave.start_time, "strftime") else (leave.start_time if leave.start_time else None)),
            "end_time": (leave.end_time.strftime("%H:%M") if hasattr(leave.end_time, "strftime") else (leave.end_time if leave.end_time else None)),
            "category": leave.category,
            "reason": leave.reason or "",
            "status": leave.status,
            "total_minutes": leave.total_minutes,
            "worker_image": leave.worker.profile_picture.url if leave.worker.profile_picture else None,
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
            "worker_name": f"{leave.worker.first_name} {leave.worker.last_name}",
            "start_date": getattr(leave.start_date, "isoformat", lambda: str(leave.start_date))(),
            "end_date": getattr(leave.end_date, "isoformat", lambda: str(leave.end_date))(),
            "start_time": (leave.start_time.strftime("%H:%M") if hasattr(leave.start_time, "strftime") else (leave.start_time if leave.start_time else None)),
            "end_time": (leave.end_time.strftime("%H:%M") if hasattr(leave.end_time, "strftime") else (leave.end_time if leave.end_time else None)),
            "category": leave.category,
            "reason": leave.reason or "",
            "status": leave.status,
            "total_minutes": leave.total_minutes,
            "worker_image": leave.worker.profile_picture.url if leave.worker.profile_picture else None,
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
                "worker_name": f"{leave.worker.first_name} {leave.worker.last_name}",
                "start_date": getattr(leave.start_date, "isoformat", lambda: str(leave.start_date))(),
                "end_date": getattr(leave.end_date, "isoformat", lambda: str(leave.end_date))(),
                "start_time": (leave.start_time.strftime("%H:%M") if hasattr(leave.start_time, "strftime") else (leave.start_time if leave.start_time else None)),
                "end_time": (leave.end_time.strftime("%H:%M") if hasattr(leave.end_time, "strftime") else (leave.end_time if leave.end_time else None)),
                "category": leave.category,
                "reason": leave.reason or "",
                "status": leave.status,
                "total_minutes": leave.total_minutes,
                "worker_image": leave.worker.profile_picture.url if leave.worker.profile_picture else None,
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
                'base_price': request.POST.get('price') or 0,
            }
        )
        
        if not _:
            product.base_price = request.POST.get('price') or 0
            product.save()

        indexes = request.POST.getlist('variant_index')
        colors = request.POST.getlist('variant_color')
        sizes = request.POST.getlist('variant_size')
        prices = request.POST.getlist('variant_price')
        stocks = request.POST.getlist('variant_stock')
        skus = request.POST.getlist('variant_sku')
        scent_names = request.POST.getlist('variant_scent_name')
        variant_descriptions = request.POST.getlist('variant_description')
        media_indexes = request.POST.getlist('variant_media_index')

        spec_names = request.POST.getlist('spec_name')
        spec_values = request.POST.getlist('spec_value')
        
        layer = get_channel_layer()

        if colors:
            color_variants = {}
            color_gallery_source = {}
            for i in range(len(colors)):
                idx = indexes[i] if i < len(indexes) else i
                media_idx = media_indexes[i] if i < len(media_indexes) and media_indexes[i] else idx
                color_name = colors[i].strip() or 'Default'
                color_key = color_name.strip().lower()
                size_name = sizes[i].strip() if i < len(sizes) else 'Default'
                size_name = size_name or 'Default'
                price_val = prices[i] if i < len(prices) and prices[i] else 0
                stock_val = stocks[i] if i < len(stocks) and stocks[i] else 0
                scent_name = scent_names[i] if i < len(scent_names) else ''
                v_description = variant_descriptions[i] if i < len(variant_descriptions) else ''
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
                        'sku': sku,
                        'scent_name': scent_name,
                        'description': v_description
                    }
                )
                if not created:
                    variant.price = price_val
                    variant.stock = stock_val
                    variant.sku = sku
                    variant.scent_name = scent_name
                    variant.description = v_description
                    variant.save()
                    
                v_image = request.FILES.get(f'variant_image_{media_idx}')
                if v_image:
                    variant.image = v_image
                    variant.save()
                    # If product has no image, use the first variant's image as default
                    if not product.image:
                        product.image = v_image
                        product.save()
                    
                v_galleries = request.FILES.getlist(f'variant_gallery_{media_idx}')
                for gi in v_galleries:
                    if gi:
                        VariantImage.objects.create(variant=variant, image=gi)
                        color_gallery_source[color_key] = variant.id

                if color_key not in color_variants:
                    color_variants[color_key] = []
                color_variants[color_key].append(variant)

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
            for color_key, variants_in_color in color_variants.items():
                source_variant_with_image = next((v for v in variants_in_color if v.image), None)
                if source_variant_with_image:
                    for target_variant in variants_in_color:
                        if not target_variant.image:
                            target_variant.image = source_variant_with_image.image.name
                            target_variant.save(update_fields=['image'])
                source_variant_id = color_gallery_source.get(color_key)
                if source_variant_id:
                    source_gallery = list(VariantImage.objects.filter(variant_id=source_variant_id))
                    if source_gallery:
                        for target_variant in variants_in_color:
                            if VariantImage.objects.filter(variant=target_variant).exists():
                                continue
                            for source_img in source_gallery:
                                VariantImage.objects.create(variant=target_variant, image=source_img.image.name)
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
                variant.scent_name = request.POST.get('scent_name')
                variant.description = request.POST.get('variant_description') or request.POST.get('description', '')
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

        messages.success(request, "Inventory added successfully")
        return redirect('auth_inventory')

    categories = Category.objects.filter(status=True).order_by('name')
    return render(request, 'add_inventory.html', {'categories': categories})

@never_cache
@login_required(login_url='auth_login')
def auth_inventory(request):
    product_list = Product.objects.select_related(
        'brand',
        'brand__subcetegory',
        'brand__subcetegory__category'
    ).order_by('-id')

    paginator = Paginator(product_list, 10)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    variants = ProductVariant.objects.filter(product__in=products_page).select_related(
        'product',
        'color',
        'size',
        'product__brand',
        'product__brand__subcetegory',
        'product__brand__subcetegory__category'
    )

    categories = Category.objects.filter(status=True).order_by('name')

    groups_map = {}
    groups = []
    
    for p in products_page:
        g = {
            'product': p,
            'variants': [],
            'colors_seen': set(),
            'sizes_seen': set(),
            'unique_color_variants': [],
            'unique_size_variants': [],
        }
        groups_map[p.id] = g
        groups.append(g)

    for v in variants:
        g = groups_map.get(v.product_id)
        if g is not None:
            g['variants'].append(v)
            if v.color.name not in g['colors_seen']:
                g['colors_seen'].add(v.color.name)
                g['unique_color_variants'].append(v)
            if v.size.name not in g['sizes_seen']:
                g['sizes_seen'].add(v.size.name)
                g['unique_size_variants'].append(v)

    # Calculate total stock per group
    for g in groups:
        g['total_stock'] = sum(v.stock for v in g['variants'])

    groups = [g for g in groups if g['variants']]

    return render(request, 'auth_inventory.html', {
        'inventorys': products_page,
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
        product.base_price = request.POST.get('price') or 0
        product.save()

        color_names = request.POST.getlist('variant_color')
        size_names = request.POST.getlist('variant_size')
        price_vals = request.POST.getlist('variant_price')
        stock_vals = request.POST.getlist('variant_stock')
        scent_vals = request.POST.getlist('variant_scent_name')
        desc_vals = request.POST.getlist('variant_description')

        # Fallback to single fields if variant_color list is empty
        color_name = (color_names[0] if color_names else request.POST.get('color', '')).strip()
        size_name = (size_names[0] if size_names else request.POST.get('size', '')).strip()
        price_val = (price_vals[0] if price_vals else request.POST.get('price')) or 0
        stock_val = (stock_vals[0] if stock_vals else request.POST.get('stock')) or 0
        scent_val = (scent_vals[0] if scent_vals else request.POST.get('scent_name')) or ''
        desc_val = (desc_vals[0] if desc_vals else request.POST.get('description')) or ''

        if not color_name:
            color_name = 'Default'
        color, _ = Color.objects.get_or_create(
            name=color_name
        )

        if not size_name:
            size_name = 'Default'
        size, _ = Size.objects.get_or_create(
            name=size_name
        )

        inventory.product = product
        inventory.color = color
        inventory.size = size
        inventory.price = price_val
        inventory.stock = stock_val
        inventory.scent_name = scent_val
        inventory.description = desc_val
        inventory.sku = f"{product.id}-{color.id}-{size.id}"
        inventory.save()
        
        indexes = request.POST.getlist('variant_index')
        idx = indexes[0] if indexes else 0
        
        # 1. Handle Main Image Deletion/Update
        delete_main = request.POST.get(f'delete_variant_main_{idx}') == 'true'
        v_image = request.FILES.get(f'variant_image_{idx}')
        
        if v_image:
            # New image uploaded - update and save
            inventory.image = v_image
            inventory.save()
            # If product has no image, use the edited variant's image as default
            if not product.image:
                product.image = v_image
                product.save()
        elif delete_main:
            # Explicit delete requested
            if inventory.image:
                # Permanent deletion from disk (optional but requested "permanently")
                inventory.image.delete(save=False)
                inventory.image = None
                inventory.save()

        # 2. Sync image color-wise
        color_variants = ProductVariant.objects.filter(
            product=product,
            color=color
        ).exclude(id=inventory.id)
        
        for v in color_variants:
            # Sync main image
            v.image = inventory.image
            v.save()
            
        # 3. Handle Gallery Deletions
        delete_gallery_urls = request.POST.getlist(f'delete_variant_gallery_{idx}')
        import os
        for url in delete_gallery_urls:
            if url:
                # Find the VariantImage by filename comparison for robustness
                target_filename = os.path.basename(url.split('?')[0])
                for vi in VariantImage.objects.filter(variant=inventory):
                    if vi.image:
                        vi_filename = os.path.basename(vi.image.name)
                        if vi_filename == target_filename or url.endswith(vi.image.url):
                            vi.image.delete(save=False)
                            vi.delete()
                            break
            
        # 4. Handle Gallery Additions
        v_galleries = request.FILES.getlist(f'variant_gallery_{idx}')
        new_gallery_added = False
        for gi in v_galleries:
            if gi:
                VariantImage.objects.create(variant=inventory, image=gi)
                new_gallery_added = True

        # 5. Sync gallery color-wise
        if delete_gallery_urls or new_gallery_added:
            source_gallery = list(VariantImage.objects.filter(variant=inventory))
            for v in color_variants:
                # Clear target gallery
                # Important: delete files only if they are not the ones we just kept
                VariantImage.objects.filter(variant=v).delete()
                for source_img in source_gallery:
                    # Point to the same file
                    VariantImage.objects.create(variant=v, image=source_img.image.name)

        spec_names = request.POST.getlist('spec_name')
        spec_values = request.POST.getlist('spec_value')
        VariantSpec.objects.filter(variant=inventory).delete()
        for name, value in zip(spec_names, spec_values):
            name = (name or '').strip()
            value = (value or '').strip()
            if name and value:
                VariantSpec.objects.create(variant=inventory, name=name, value=value)

        layer = get_channel_layer()
        if layer:
            payload = {
                "id": inventory.id,
                "product_name": product.name,
                "brand_name": product.brand.name,
                "category_name": product.brand.subcetegory.category.name,
                "price": float(inventory.price),
                "stock": inventory.stock,
                "image_url": inventory.image.url if inventory.image else None,
            }
            async_to_sync(layer.group_send)("inventory", {
                "type": "inventory_updated",
                "inventory": payload,
            })

        messages.success(request, "Inventory updated successfully")
        return redirect('auth_inventory')

    categories = Category.objects.filter(status=True).order_by('name')
    return render(request, 'edit_inventory.html', {
        'inventory': inventory,
        'categories': categories
    })

@never_cache
@login_required(login_url='auth_login')
def view_inventory(request, id):
    inventory = get_object_or_404(ProductVariant, id=id)
    # Get all variants of the same product for comparison if needed
    product_variants = ProductVariant.objects.filter(product=inventory.product).select_related('color', 'size')
    
    return render(request, 'view_inventory.html', {
        'inventory': inventory,
        'product_variants': product_variants
    })

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
            title=request.POST.get('title'),
            image=request.FILES.get('image'),
            des=request.POST.get('des'),
            by=request.POST.get('by'),
            date=request.POST.get('date'), 
        )
        layer = get_channel_layer()
        if layer:
            data = {
                "id": blog.id,
                "title": blog.title,
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
        blog.title = request.POST.get('title')
        blog.des = request.POST.get('des')
        blog.by = request.POST.get('by')
        blog.date = request.POST.get('date')

        if request.POST.get('remove_image') == 'true':
            blog.image = None

        if request.FILES.get('image'):
            blog.image = request.FILES.get('image')

        blog.save()
        layer = get_channel_layer()
        if layer:
            data = {
                "id": blog.id,
                "title": blog.title,
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

@never_cache
@login_required(login_url='auth_login')
def auth_sliders(request):
    slider_list = Slider.objects.all().order_by('order', '-created_at')
    
    # Pagination
    paginator = Paginator(slider_list, 10)  # Show 10 sliders per page
    page_number = request.GET.get('page')
    sliders = paginator.get_page(page_number)
    
    return render(request, 'auth_sliders.html', {'sliders': sliders})

@never_cache
@login_required(login_url='auth_login')
def add_slider(request):
    if request.method == "POST":
        Slider.objects.create(
            image=request.FILES.get('image'),
            title=request.POST.get('title'),
            subtitle=request.POST.get('subtitle', ''),
            button_text=request.POST.get('button_text', ''),
            button_link=request.POST.get('button_link', ''),
            order=request.POST.get('order', 0) or 0,
            status=request.POST.get('status') == 'on'
        )

    return redirect('auth_sliders')

@never_cache
@login_required(login_url='auth_login')
def edit_slider(request, id):
    slider = get_object_or_404(Slider, id=id)
    if request.method == "POST":
        if request.FILES.get('image'):
            slider.image = request.FILES.get('image')
        slider.title = request.POST.get('title')
        slider.subtitle = request.POST.get('subtitle', '')
        slider.button_text = request.POST.get('button_text', '')
        slider.button_link = request.POST.get('button_link', '')
        slider.order = request.POST.get('order', 0) or 0
        slider.status = request.POST.get('status') == 'on'
        slider.save()

    return redirect('auth_sliders')

@never_cache
@login_required(login_url='auth_login')
def delete_slider(request, id):
    Slider.objects.filter(id=id).delete()

    return redirect('auth_sliders')

@never_cache
@login_required(login_url='auth_login')
def toggle_slider_status(request, id):
    slider = get_object_or_404(Slider, id=id)
    slider.status = not slider.status
    slider.save()
    return JsonResponse({'status': 'success', 'new_status': slider.status})

@never_cache
@login_required(login_url='auth_login')
def delete_product_inventory(request, product_id):
    # This deletes the entire product and all its variants
    Product.objects.filter(id=product_id).delete()
    
    layer = get_channel_layer()
    if layer:
        # We notify about deletion. Since multiple variants might be gone, 
        # a simple refresh on the buyer side is often easiest.
        async_to_sync(layer.group_send)("inventory", {
            "type": "inventory_deleted",
            "product_id": product_id,
        })

    return redirect('auth_inventory')

@never_cache
@login_required(login_url='auth_login')
def auth_profile(request):
    user = request.user
    profile, _ = AdminProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()

        profile.phone = request.POST.get('phone', profile.phone)
        profile.address = request.POST.get('address', profile.address)
        
        if request.FILES.get('profile_image'):
            profile.profile_image = request.FILES['profile_image']
            
        profile.save()
        messages.success(request, "Admin Profile updated successfully")
        return redirect(request.META.get('HTTP_REFERER', 'auth_dashboard'))
        
    return redirect(request.META.get('HTTP_REFERER', 'auth_dashboard'))