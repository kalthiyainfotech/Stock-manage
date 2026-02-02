from django.urls import path
from admin_panel.views import *

urlpatterns = [
    path('auth_login/',auth_login,name='auth_login'),
    path('auth_dashboard/',auth_dashboard,name='auth_dashboard'),
    path('auth_logout/',auth_logout,name='auth_logout'),
    path('auth_suppliers/',auth_suppliers,name='auth_suppliers'),
    path('add-supplier/', add_supplier, name='add_supplier'),
    path('supplier/edit/<int:id>/', edit_supplier, name='edit_supplier'),
    path('supplier/delete/<int:id>/', delete_supplier, name='delete_supplier'),


    path('auth_workers/',auth_workers,name='auth_workers'),
    path('add-worker/', add_worker, name='add_worker'),
    path('worker/edit/<int:id>/', edit_worker, name='edit_worker'),
    path('worker/delete/<int:id>/', delete_worker, name='delete_worker'),


    path('auth_inventory/',auth_inventory,name='auth_inventory'),
    path('add_inventory/',add_inventory,name='add_inventory'),
    path('edit/inventory/<int:id>/',edit_inventory,name='edit_inventory'),
    path('delete/inventory/<int:id>/',delete_inventory,name='delete_inventory'),


    path('auth_buyers/',auth_buyers,name='auth_buyers'),


]
