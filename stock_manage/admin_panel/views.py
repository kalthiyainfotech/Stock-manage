from django.shortcuts import render , redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required

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
    return render(request,'auth_suppliers.html')

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





