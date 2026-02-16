from django.shortcuts import render , redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import *
from buyers.models import Buyer, Order

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
            messages.error(request, "Invalid credentials")

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






# Suppliers Views

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
        Suppliers.objects.create(
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

    return redirect('auth_suppliers')

@never_cache
@login_required(login_url='auth_login')
def delete_supplier(request, id):
    Suppliers.objects.filter(id=id).delete()
    return redirect('auth_suppliers')








# Workers Views

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
        Holiday.objects.create(
            name=request.POST['name'],
            date=request.POST['date'],
            description=request.POST.get('description', '')
        )
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
    return redirect('auth_holiday')

@never_cache
@login_required(login_url='auth_login')
def delete_holiday(request, id):
    Holiday.objects.filter(id=id).delete()
    return redirect('auth_holiday')








@never_cache
@login_required(login_url='auth_login')
def add_inventory(request):
    if request.method == "POST":

        category_name = request.POST.get('new_category') or request.POST.get('category')
        if not category_name:
            messages.error(request, "Category is required")
            return redirect('auth_inventory')
        
        category, _ = Category.objects.get_or_create(
            name=category_name
        )

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
                'image': request.FILES.get('product_picture')
            }
        )
        
        if not _:
            product.description = request.POST.get('description', '')
            product.base_price = request.POST.get('price') or 0
            if request.FILES.get('product_picture'):
                product.image = request.FILES.get('product_picture')
            product.save()

        color_name = request.POST.get('color', '').strip()
        if not color_name:
            color_name = 'Default'
        color, _ = Color.objects.get_or_create(
            name=color_name
        )

        size_name = request.POST.get('size', '').strip()
        if not size_name:
            size_name = 'Default'
        size, _ = Size.objects.get_or_create(
            name=size_name
        )

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

        spec_names = request.POST.getlist('spec_name')
        spec_values = request.POST.getlist('spec_value')
        VariantSpec.objects.filter(variant=variant).delete()
        for name, value in zip(spec_names, spec_values):
            name = (name or '').strip()
            value = (value or '').strip()
            if name and value:
                VariantSpec.objects.create(variant=variant, name=name, value=value)

        messages.success(request, "Inventory added successfully")
        return redirect('auth_inventory')

    return redirect('auth_inventory')



@never_cache
@login_required(login_url='auth_login')
def auth_inventory(request):
    inventory_list = ProductVariant.objects.select_related(
        'product',
        'color',
        'size',
        'product__brand',
        'product__brand__subcetegory',
        'product__brand__subcetegory__category'
    ).order_by('-id')

    paginator = Paginator(inventory_list, 10)
    page_number = request.GET.get('page')
    inventory = paginator.get_page(page_number)

    categories = Category.objects.filter(status=True).order_by('name')

    return render(request, 'auth_inventory.html', {
        'inventorys': inventory,  
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
        
        category, _ = Category.objects.get_or_create(
            name=category_name
        )

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

        if request.FILES.get('product_picture'):
            product.image = request.FILES.get('product_picture')

        product.save()

        color_name = request.POST.get('color', '').strip()
        if not color_name:
            color_name = 'Default'
        color, _ = Color.objects.get_or_create(
            name=color_name
        )

        size_name = request.POST.get('size', '').strip()
        if not size_name:
            size_name = 'Default'
        size, _ = Size.objects.get_or_create(
            name=size_name
        )

        inventory.product = product
        inventory.color = color
        inventory.size = size
        inventory.price = request.POST.get('price') or 0
        inventory.stock = request.POST.get('stock') or 0
        inventory.sku = f"{product.id}-{color.id}-{size.id}"
        inventory.save()

        spec_names = request.POST.getlist('spec_name')
        spec_values = request.POST.getlist('spec_value')
        VariantSpec.objects.filter(variant=inventory).delete()
        for name, value in zip(spec_names, spec_values):
            name = (name or '').strip()
            value = (value or '').strip()
            if name and value:
                VariantSpec.objects.create(variant=inventory, name=name, value=value)

        messages.success(request, "Inventory updated successfully")
        return redirect('auth_inventory')

    return redirect('auth_inventory')



@never_cache
@login_required(login_url='auth_login')
def delete_inventory(request, id):
    inventory = ProductVariant.objects.get(id=id)
    inventory.delete()
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







# Blogs

@never_cache
@login_required(login_url='auth_login')
def auth_blogs(request):
    blogs_list = Blogs.objects.all().order_by('-id')

    paginator = Paginator(blogs_list, 5)
    page_number = request.GET.get('page')
    blogs = paginator.get_page(page_number)

    return render(request, 'auth_blogs.html', {
        'blogs': blogs
    })


@never_cache
@login_required(login_url='auth_login')
def add_blogs(request):
    if request.method == "POST":
        Blogs.objects.create(
            image=request.FILES.get('image'),
            des=request.POST.get('des'),
            by=request.POST.get('by'),
            date=request.POST.get('date'),
        )
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

    return redirect('auth_blogs')


@never_cache
@login_required(login_url='auth_login')
def delete_blogs(request, id):
    Blogs.objects.filter(id=id).delete()
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
    Order.objects.filter(id=id).delete()
    return redirect('auth_order')





