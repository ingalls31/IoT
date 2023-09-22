from django.urls import re_path, path

from . import tunnel

websocket_urlpatterns = [
    re_path(r"ws/dht11/$", tunnel.DHT11.as_asgi()),
]
