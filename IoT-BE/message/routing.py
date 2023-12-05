from django.urls import re_path

# from . import tunnel
from . import consumers

websocket_urlpatterns = [
    # re_path(r"ws/dht11/$", tunnel.DHT11.as_asgi()),
    re_path(r'ws/sensor/', consumers.SensorConsumer.as_asgi()),
    re_path(r'ws/relay/', consumers.RelayConsumer.as_asgi()),
    re_path(r'ws/auto/', consumers.AutoMLConsumer.as_asgi()),
    re_path(r'ws/water/', consumers.WaterConsumer.as_asgi())
]
