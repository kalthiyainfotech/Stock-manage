from django.shortcuts import render, redirect
from django.contrib import messages
from admin_panel.models import Suppliers
from functools import wraps
from django.views.decorators.cache import never_cache
from buyers.models import Order
from django.http import HttpResponseForbidden
from django.db.models import F


def supplier_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'supplier_id' not in request.session:
            messages.error(request, "Please login to access this page", extra_tags="supplier")
            return redirect('supplier_login')
        return view_func(request, *args, **kwargs)
    return wrapper

@never_cache
def supplier_login(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if not email or not password:
            messages.error(request, "Please provide both email and password", extra_tags="supplier")
            return render(request, 'sup_login.html')

        try:
            supplier = Suppliers.objects.get(email=email)
            
            if supplier.password != password:
                messages.error(request, "Invalid email or password", extra_tags="supplier")
                return render(request, 'sup_login.html')
            
            if supplier.status != "Active":
                messages.error(request, "Account is inactive. Please contact administrator.", extra_tags="supplier")
                return render(request, 'sup_login.html')
            
            request.session['supplier_id'] = supplier.id
            request.session['supplier_email'] = supplier.email
            request.session['supplier_name'] = supplier.name
            messages.success(request, f"Welcome back, {supplier.name}!", extra_tags="supplier")
            return redirect('supplier_dashboard')

        except Suppliers.DoesNotExist:
            messages.error(request, "Invalid email or password. This email is not assigned by admin.", extra_tags="supplier")
        except Exception as e:
            messages.error(request, "An error occurred. Please try again.", extra_tags="supplier")
    
    return render(request, 'sup_login.html')

@never_cache
@supplier_login_required
def sup_dash(request):
    supplier_id = request.session.get('supplier_id')
    try:
        supplier = Suppliers.objects.get(id=supplier_id)
        orders = Order.objects.prefetch_related(
            "items",
            "items__variant",
            "items__variant__product"
        ).order_by("-created_at")
        delivered_count = Order.objects.filter(status="delivered").count()
        shipped_count = Order.objects.filter(status="shipped").count()
        return_requested_count = Order.objects.filter(status="return_requested").count()
        context = {
            'supplier': supplier,
            'orders': orders,
            'ORDER_STATUS_CHOICES': Order.ORDER_STATUS_CHOICES,
            'delivered_count': delivered_count,
            'shipped_count': shipped_count,
            'return_requested_count': return_requested_count,
        }
        return render(request, 'sup_dash.html', context)
    except Suppliers.DoesNotExist:
        messages.error(request, "Supplier account not found", extra_tags="supplier")
        return redirect('supplier_login')

@never_cache
@supplier_login_required
def sup_orders(request):
    supplier_id = request.session.get('supplier_id')
    try:
        supplier = Suppliers.objects.get(id=supplier_id)
        orders = Order.objects.exclude(status__in=["return_requested", "returned"]).prefetch_related(
            "items",
            "items__variant",
            "items__variant__product"
        ).order_by("-created_at")
        choices_no_returns = [c for c in Order.ORDER_STATUS_CHOICES if c[0] not in ("return_requested", "returned")]
        context = {
            'supplier': supplier,
            'orders': orders,
            'ORDER_STATUS_CHOICES_NO_RETURNS': choices_no_returns
        }
        return render(request, 'sup_oders.html', context)
    except Suppliers.DoesNotExist:
        messages.error(request, "Supplier account not found", extra_tags="supplier")
        return redirect('supplier_login')

@never_cache
@supplier_login_required
def sup_return_orders(request):
    supplier_id = request.session.get('supplier_id')
    try:
        supplier = Suppliers.objects.get(id=supplier_id)
        orders = Order.objects.filter(status__in=["return_requested", "returned"]).prefetch_related(
            "items",
            "items__variant",
            "items__variant__product"
        ).order_by("-created_at")
        context = {
            'supplier': supplier,
            'orders': orders,
            'ORDER_STATUS_CHOICES': Order.ORDER_STATUS_CHOICES
        }
        return render(request, 'sup_cel_orders.html', context)
    except Suppliers.DoesNotExist:
        messages.error(request, "Supplier account not found")
        return redirect('supplier_login')

@never_cache
@supplier_login_required
def sup_update_order_status(request, order_id):
    if request.method != "POST":
        return redirect('supplier_orders')
    try:
        new_status = request.POST.get("status", "").strip()
        valid_statuses = [s[0] for s in Order.ORDER_STATUS_CHOICES]
        if new_status not in valid_statuses:
            messages.error(request, "Invalid status")
            return redirect('supplier_orders')
        order = Order.objects.get(id=order_id)
        previous_status = order.status
        order.status = new_status
        order.save()
        if new_status == "returned" and previous_status in ("return_requested", "delivered"):
            for item in order.items.all():
                item.variant.__class__.objects.filter(id=item.variant_id).update(stock=F('stock') + item.quantity)
        messages.success(request, f"Order {order.order_number} updated to {order.get_status_display()}")
    except Order.DoesNotExist:
        messages.error(request, "Order not found")
    return redirect('supplier_orders')

@never_cache
@supplier_login_required
def sup_delete_order(request, order_id):
    if request.method != "POST":
        return HttpResponseForbidden()
    try:
        order = Order.objects.get(id=order_id) 
        order_number = order.order_number
        order.delete()
        messages.success(request, f"Order {order_number} deleted")
    except Order.DoesNotExist:
        messages.error(request, "Order not found")
    return redirect('supplier_orders')
@never_cache
def supplier_logout(request):
    if 'supplier_id' in request.session:
        supplier_name = request.session.get('supplier_name', '')
        request.session.pop('supplier_id', None)
        request.session.pop('supplier_email', None)
        request.session.pop('supplier_name', None)
        messages.success(request, f"Logged out successfully. Goodbye, {supplier_name}!", extra_tags="supplier")
    return redirect('supplier_login')
