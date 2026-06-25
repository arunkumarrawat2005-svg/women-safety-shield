import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import tracking.routing
import emergency.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'women_safety_shield.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            tracking.routing.websocket_urlpatterns +
            emergency.routing.websocket_urlpatterns
        )
    ),
})
