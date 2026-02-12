from django.shortcuts import render, redirect
from django.contrib import messages
from admin_panel.models import Workers
from functools import wraps
from django.views.decorators.cache import never_cache


def worker_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'worker_id' not in request.session:
            messages.error(request, "Please login to access this page")
            return redirect('worker_login')
        return view_func(request, *args, **kwargs)
    return wrapper

@never_cache
def worker_login(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if not email or not password:
            messages.error(request, "Please provide both email and password")
            return render(request, 'wk_login.html')

        try:
            worker = Workers.objects.get(email=email)
            
            if worker.password != password:
                messages.error(request, "Invalid email or password")
                return render(request, 'wk_login.html')
            
            if worker.status != "Active":
                messages.error(request, "Account is inactive. Please contact administrator.")
                return render(request, 'wk_login.html')
            
            request.session['worker_id'] = worker.id
            request.session['worker_email'] = worker.email
            request.session['worker_name'] = worker.name
            messages.success(request, f"Welcome back, {worker.name}!")
            return redirect('work_dash')

        except Workers.DoesNotExist:
            messages.error(request, "Invalid email or password. This email is not assigned by admin.")
        except Exception as e:
            messages.error(request, "An error occurred. Please try again.")

    return render(request, 'wk_login.html')

@never_cache
@worker_login_required
def work_dash(request):
    worker_id = request.session.get('worker_id')
    try:
        worker = Workers.objects.get(id=worker_id)
        context = {
            'worker': worker
        }
        return render(request, 'wk_dash.html', context)
    except Workers.DoesNotExist:
        messages.error(request, "worker account not found")
        return redirect('worker_login')

@never_cache
def worker_logout(request):
    if 'worker_id' in request.session:
        worker_name = request.session.get('worker_name', '')
        request.session.pop('worker_id', None)
        request.session.pop('worker_email', None)
        request.session.pop('worker_name', None)
        messages.success(request, f"Logged out successfully. Goodbye, {worker_name}!")
    return redirect('worker_login')
