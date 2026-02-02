from django.shortcuts import render , redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import *

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
    logout(request)
    request.session.flush()
    return redirect('auth_login')

@never_cache
@login_required(login_url='auth_login')
def auth_dashboard(request):
    return render(request,'auth_dashboard.html')






# Suppliers Views

@never_cache
@login_required(login_url='auth_login')
def auth_suppliers(request):
    supplier_list = Suppliers.objects.all().order_by('-id')

    paginator = Paginator(supplier_list, 10)  
    page_number = request.GET.get('page')
    suppliers = paginator.get_page(page_number)

    return render(request, 'auth_suppliers.html', {
        'suppliers': suppliers
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
def add_inventory(request):
    if request.method == "POST":

        # CATEGORY
        category, _ = Category.objects.get_or_create(
            name=request.POST['category']
        )

        # SUBCATEGORY
        subcategory, _ = Subcetegory.objects.get_or_create(
            category=category,
            name=request.POST['subcategory']
        )

        # BRAND
        brand, _ = Brand.objects.get_or_create(
            subcetegory=subcategory,
            name=request.POST['brand']
        )

        # PRODUCT
        product, _ = Product.objects.get_or_create(
            brand=brand,
            name=request.POST['product'],
            defaults={
                'description': request.POST.get('description', ''),
                'base_price': request.POST.get('price') or 0,
                'image': request.FILES.get('product_picture')
            }
        )

        # COLOR
        color, _ = Color.objects.get_or_create(
            name=request.POST.get('color')
        )

        # SIZE
        size, _ = Size.objects.get_or_create(
            name=request.POST.get('size')
        )

        # PRODUCT VARIANT
        ProductVariant.objects.create(
            product=product,
            color=color,
            size=size,
            price=request.POST.get('price') or 0,
            stock=request.POST.get('stock') or 0,
            sku=f"{product.id}-{color.id}-{size.id}"
        )

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

    return render(request, 'auth_inventory.html', {
        'inventorys': inventory  # KEEP NAME to avoid HTML change
    })


@never_cache
@login_required(login_url='auth_login')
def edit_inventory(request, id):
    inventory = ProductVariant.objects.get(id=id)

    if request.method == "POST":

        # CATEGORY
        category, _ = Category.objects.get_or_create(
            name=request.POST['category']
        )

        # SUBCATEGORY
        subcategory, _ = Subcetegory.objects.get_or_create(
            category=category,
            name=request.POST['subcategory']
        )

        # BRAND
        brand, _ = Brand.objects.get_or_create(
            subcetegory=subcategory,
            name=request.POST['brand']
        )

        # PRODUCT
        product = inventory.product
        product.brand = brand
        product.name = request.POST['product']
        product.description = request.POST.get('description', '')
        product.base_price = request.POST.get('price') or 0

        if request.FILES.get('product_picture'):
            product.image = request.FILES.get('product_picture')

        product.save()

        # COLOR
        color, _ = Color.objects.get_or_create(
            name=request.POST.get('color')
        )

        # SIZE
        size, _ = Size.objects.get_or_create(
            name=request.POST.get('size')
        )

        # VARIANT
        inventory.product = product
        inventory.color = color
        inventory.size = size
        inventory.price = request.POST.get('price') or 0
        inventory.stock = request.POST.get('stock') or 0
        inventory.save()

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
def auth_buyers(request):
    return render(request,'auth_buyers.html')







