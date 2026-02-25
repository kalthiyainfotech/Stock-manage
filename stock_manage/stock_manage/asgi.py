"""
ASGI config for stock_manage project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import stock_manage.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_manage.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(stock_manage.routing.websocket_urlpatterns),
})
