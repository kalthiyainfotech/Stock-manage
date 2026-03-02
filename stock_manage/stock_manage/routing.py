from django.urls import path
from buyers.consumers import BlogConsumer, CategoryConsumer

websocket_urlpatterns = [
    path('ws/blogs/', BlogConsumer.as_asgi()),
    path('ws/categories/', CategoryConsumer.as_asgi()),
]
