import os

from channels.routing import URLRouter, ProtocolTypeRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from message import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot.settings')
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # "websocket": URLRouter(routing.websocket_urlpatterns)
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    )
})
