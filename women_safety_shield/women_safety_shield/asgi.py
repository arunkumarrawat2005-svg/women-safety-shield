import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'women_safety_shield.women_safety_shield.settings')

django_asgi_app = get_asgi_application()

import tracking.routing
import emergency.routing

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            tracking.routing.websocket_urlpatterns +
            emergency.routing.websocket_urlpatterns
        )
    ),
})
