from django.urls import path
from suppliers.views import supplier_login,sup_dash,supplier_logout
from suppliers.views import sup_update_order_status,sup_delete_order


urlpatterns = [
    path('',supplier_login,name='supplier_login'),
    path('supplier/dashboard',sup_dash,name='supplier_dashboard'),
    path('supplier/logout',supplier_logout,name='supplier_logout'),
    path('supplier/order/<int:order_id>/update-status/', sup_update_order_status, name='sup_update_order_status'),
    path('supplier/order/<int:order_id>/delete/', sup_delete_order, name='sup_delete_order'),
]
