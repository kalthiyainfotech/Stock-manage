from django.urls import path
from suppliers.views import (
    supplier_login, sup_dash, supplier_logout,
    sup_update_order_status, sup_delete_order,
    sup_orders, sup_return_orders, sup_dash_stats_api
)


urlpatterns = [
    path('',supplier_login,name='supplier_login'),
    path('supplier/dashboard',sup_dash,name='supplier_dashboard'),
    path('supplier/dashboard/stats/', sup_dash_stats_api, name='sup_dash_stats_api'),
    path('supplier/orders', sup_orders, name='supplier_orders'),
    path('supplier/returns', sup_return_orders, name='supplier_returns'),
    path('supplier/logout',supplier_logout,name='supplier_logout'),
    path('supplier/order/<int:order_id>/update-status/', sup_update_order_status, name='sup_update_order_status'),
    path('supplier/order/<int:order_id>/delete/', sup_delete_order, name='sup_delete_order'),
]
