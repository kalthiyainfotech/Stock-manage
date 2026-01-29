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

@never_cache
@login_required(login_url='auth_login')
def auth_suppliers(request):
    supplier_list = Suppliers.objects.all().order_by('-id')

    paginator = Paginator(supplier_list, 10)  # ✅ 10 per page
    page_number = request.GET.get('page')
    suppliers = paginator.get_page(page_number)

    return render(request, 'auth_suppliers.html', {
        'suppliers': suppliers
    })

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

def delete_supplier(request, id):
    Suppliers.objects.filter(id=id).delete()
    return redirect('auth_suppliers')


@never_cache
@login_required(login_url='auth_login')
def auth_buyers(request):
    return render(request,'auth_buyers.html')

@never_cache
@login_required(login_url='auth_login')
def auth_inventory(request):
    return render(request,'auth_inventory.html')

@never_cache
@login_required(login_url='auth_login')
def auth_workers(request):
    return render(request,'auth_workers.html')





