from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/emergency/(?P<emergency_id>\d+)/$', consumers.EmergencyConsumer.as_asgi()),
]
