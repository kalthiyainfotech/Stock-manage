from django.urls import path
from suppliers.views import supplier_login,sup_dash,supplier_logout


urlpatterns = [
    path('',supplier_login,name='supplier_login'),
    path('supplier/dashboard',sup_dash,name='supplier_dashboard'),
    path('supplier/logout',supplier_logout,name='supplier_logout')
]
