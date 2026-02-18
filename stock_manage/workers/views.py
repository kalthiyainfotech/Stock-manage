from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from admin_panel.models import Workers, Holiday, Leave
from functools import wraps
from django.views.decorators.cache import never_cache


def worker_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'worker_id' not in request.session:
            messages.error(request, "Please login to access this page", extra_tags="worker")
            return redirect('worker_login')
        return view_func(request, *args, **kwargs)
    return wrapper

@never_cache
def worker_login(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if not email or not password:
            messages.error(request, "Please provide both email and password", extra_tags="worker")
            return render(request, 'wk_login.html')

        try:
            worker = Workers.objects.get(email=email)
            
            if worker.password != password:
                messages.error(request, "Invalid email or password", extra_tags="worker")
                return render(request, 'wk_login.html')
            
            if worker.status != "Active":
                messages.error(request, "Account is inactive. Please contact administrator.", extra_tags="worker")
                return render(request, 'wk_login.html')
            
            request.session['worker_id'] = worker.id
            request.session['worker_email'] = worker.email
            request.session['worker_name'] = worker.name
            messages.success(request, f"Welcome back, {worker.name}!", extra_tags="worker")
            return redirect('work_dash')

        except Workers.DoesNotExist:
            messages.error(request, "Invalid email or password. This email is not assigned by admin.", extra_tags="worker")
        except Exception as e:
            messages.error(request, "An error occurred. Please try again.", extra_tags="worker")

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
        messages.error(request, "worker account not found", extra_tags="worker")
        return redirect('worker_login')

@never_cache
def worker_logout(request):
    if 'worker_id' in request.session:
        worker_name = request.session.get('worker_name', '')
        request.session.pop('worker_id', None)
        request.session.pop('worker_email', None)
        request.session.pop('worker_name', None)
        messages.success(request, f"Logged out successfully. Goodbye, {worker_name}!", extra_tags="worker")
    return redirect('worker_login')

@never_cache
@worker_login_required
def holidays_api(request):
    try:
        year = int(request.GET.get('year'))
        month = int(request.GET.get('month'))
    except (TypeError, ValueError):
        today = __import__('datetime').date.today()
        year = today.year
        month = today.month

    holidays = Holiday.objects.filter(date__year=year, date__month=month).order_by('date')
    data = [
        {
            "date": h.date.isoformat(),
            "name": h.name,
            "description": h.description or ""
        }
        for h in holidays
    ]
    return JsonResponse({"holidays": data})

@never_cache
@worker_login_required
def leaves_api(request):
    try:
        year = int(request.GET.get('year'))
        month = int(request.GET.get('month'))
    except (TypeError, ValueError):
        today = __import__('datetime').date.today()
        year = today.year
        month = today.month
    worker_id = request.session.get('worker_id')
    worker = Workers.objects.get(id=worker_id)
    dt = __import__('datetime')
    month_start = dt.date(year, month, 1)
    if month == 12:
        next_month = dt.date(year + 1, 1, 1)
    else:
        next_month = dt.date(year, month + 1, 1)
    month_end = next_month - dt.timedelta(days=1)
    leaves = Leave.objects.filter(
        worker=worker,
        status__in=['Approved', 'Rejected'],
        start_date__lte=month_end,
        end_date__gte=month_start
    ).order_by('start_date')
    by_date = {}
    for l in leaves:
        s = l.start_date if l.start_date > month_start else month_start
        e = l.end_date if l.end_date < month_end else month_end
        cur = s
        st = (l.status or '').lower()
        while cur <= e:
            by_date[cur.isoformat()] = {"date": cur.isoformat(), "status": st}
            cur += dt.timedelta(days=1)
    return JsonResponse({"leaves": list(by_date.values())})

@never_cache
@worker_login_required
def wk_leave(request):
    worker_id = request.session.get('worker_id')
    worker = Workers.objects.get(id=worker_id)
    leaves = Leave.objects.filter(worker=worker).order_by('-created_at')
    return render(request, 'wk_leave.html', {
        'worker': worker,
        'leaves': leaves
    })

@never_cache
@worker_login_required
def add_leave(request):
    if request.method == "POST":
        worker_id = request.session.get('worker_id')
        worker = Workers.objects.get(id=worker_id)
        Leave.objects.create(
            worker=worker,
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            start_time=request.POST.get('start_time') or None,
            end_time=request.POST.get('end_time') or None,
            category=request.POST.get('category') or 'Casual',
            reason=request.POST.get('reason', ''),
            status='Pending'
        )
    return redirect('wk_leave')

@never_cache
@worker_login_required
def edit_leave(request, id):
    worker_id = request.session.get('worker_id')
    worker = Workers.objects.get(id=worker_id)
    leave = Leave.objects.filter(id=id, worker=worker).first()
    if not leave:
        messages.error(request, "Leave not found")
        return redirect('wk_leave')
    if leave.status != 'Pending':
        messages.error(request, "Only pending leave can be edited")
        return redirect('wk_leave')
    if request.method == "POST":
        leave.start_date = request.POST.get('start_date') or leave.start_date
        leave.end_date = request.POST.get('end_date') or leave.end_date
        leave.start_time = request.POST.get('start_time') or leave.start_time
        leave.end_time = request.POST.get('end_time') or leave.end_time
        category = request.POST.get('category') or leave.category
        if category in ['Sick', 'Emergency', 'Casual']:
            leave.category = category
        leave.reason = request.POST.get('reason', leave.reason)
        leave.save()
    return redirect('wk_leave')

@never_cache
@worker_login_required
def delete_leave(request, id):
    worker_id = request.session.get('worker_id')
    worker = Workers.objects.get(id=worker_id)
    leave = Leave.objects.filter(id=id, worker=worker).first()
    if not leave:
        messages.error(request, "Leave not found")
        return redirect('wk_leave')
    if leave.status != 'Pending':
        messages.error(request, "Only pending leave can be deleted")
        return redirect('wk_leave')
    Leave.objects.filter(id=id, worker=worker).delete()
    return redirect('wk_leave')
