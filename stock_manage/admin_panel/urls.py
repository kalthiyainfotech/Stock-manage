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

    path('auth_holiday/',auth_holiday,name='auth_holiday'),
    path('add-holiday/', add_holiday, name='add_holiday'),
    path('holiday/edit/<int:id>/', edit_holiday, name='edit_holiday'),
    path('holiday/delete/<int:id>/', delete_holiday, name='delete_holiday'),

    path('auth_inventory/',auth_inventory,name='auth_inventory'),
    path('add_inventory/',add_inventory,name='add_inventory'),
    path('edit/inventory/<int:id>/',edit_inventory,name='edit_inventory'),
    path('delete/inventory/<int:id>/',delete_inventory,name='delete_inventory'),

    path('auth_leaves/', auth_leaves, name='auth_leaves'),
    path('leave/approve/<int:id>/', approve_leave, name='approve_leave'),
    path('leave/reject/<int:id>/', reject_leave, name='reject_leave'),
    path('leave/edit/<int:id>/', edit_leave_admin, name='edit_leave_admin'),
    path('leave/delete/<int:id>/', delete_leave_admin, name='delete_leave_admin'),

    path('auth_buyers/',auth_buyers,name='auth_buyers'),
    path('delete/buyer/<int:id>/',delete_buyer,name='delete_buyer'),

    path('api/get-subcategories/', get_subcategories, name='get_subcategories'),
    path('api/get-brands/', get_brands, name='get_brands'),
    path('api/get-products/', get_products, name='get_products'),

    path('blogs/', auth_blogs, name='auth_blogs'),
    path('blogs/add/', add_blogs, name='add_blogs'),
    path('blogs/edit/<int:id>/', edit_blogs, name='edit_blogs'),
    path('blogs/delete/<int:id>/', delete_blogs, name='delete_blogs'),

    path('contacts/', auth_contacts, name='auth_contacts'),
    path('contacts/delete/<int:id>/', delete_contact, name='delete_contact'),

    path('orders/',auth_order,name='auth_order'),
    path('orders/delete/<int:id>/', delete_order, name='delete_order'),

]
