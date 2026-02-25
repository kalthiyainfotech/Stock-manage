from django.urls import path
from buyers.consumers import BlogConsumer

websocket_urlpatterns = [
    path('ws/blogs/', BlogConsumer.as_asgi()),
]
