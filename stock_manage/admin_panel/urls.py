from django.urls import path
from admin_panel.views import auth_login ,auth_dashboard,auth_logout,auth_suppliers,auth_buyers,auth_workers,auth_inventory

urlpatterns = [
    path('auth_login/',auth_login,name='auth_login'),
    path('auth_dashboard/',auth_dashboard,name='auth_dashboard'),
    path('auth_logout/',auth_logout,name='auth_logout'),
    path('auth_suppliers/',auth_suppliers,name='auth_suppliers'),
    path('auth_buyers/',auth_buyers,name='auth_buyers'),
    path('auth_workers/',auth_workers,name='auth_workers'),
    path('auth_inventory/',auth_inventory,name='auth_inventory'),
]
