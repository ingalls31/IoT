import os

from channels.routing import URLRouter, ProtocolTypeRouter
from django.core.asgi import get_asgi_application
from message import routing 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot.settings')
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(routing.websocket_urlpatterns)
})
