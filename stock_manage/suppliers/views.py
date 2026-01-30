from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from admin_panel.models import Suppliers
from django.contrib.auth.decorators import login_required


def supplier_login(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user:
            try:
                supplier = Suppliers.objects.get(user=user)
                if supplier.status != "Active":
                    messages.error(request, "Account is inactive")
                    return redirect('supplier_login')

                login(request, user)
                return redirect('sup_dash')

            except Suppliers.DoesNotExist:
                messages.error(request, "Not a supplier account")
        else:
            messages.error(request, "Invalid email or password")

    return render(request, 'sup_login.html')


@login_required(login_url='supplier_login')
def sup_dash(request):
    return render(request, 'supplier/sup_dash.html')