from django.urls import path
from buyers.consumers import BlogConsumer, CategoryConsumer, InventoryConsumer, OrderConsumer
from workers.consumers import HolidayConsumer, LeavesConsumer
from admin_panel.consumers import DashboardConsumer

websocket_urlpatterns = [
    path('ws/blogs/', BlogConsumer.as_asgi()),
    path('ws/categories/', CategoryConsumer.as_asgi()),
    path('ws/inventory/', InventoryConsumer.as_asgi()),
    path('ws/holidays/', HolidayConsumer.as_asgi()),
    path('ws/leaves/', LeavesConsumer.as_asgi()),
    path('ws/orders/', OrderConsumer.as_asgi()),
    path('ws/dashboard/', DashboardConsumer.as_asgi()),
]
