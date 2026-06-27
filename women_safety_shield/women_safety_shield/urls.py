from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from notifications.views import save_token
from django.http import FileResponse
import os

def serve_firebase_sw(request):
    file_path = os.path.join(settings.BASE_DIR, 'firebase-messaging-sw.js')
    return FileResponse(open(file_path, 'rb'), content_type='application/javascript')

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('accounts.urls')),
    path('emergency/', include('emergency.urls')),
    path('tracking/', include('tracking.urls')),
    path('community/', include('community.urls')),
    path('guardians/', include('guardians.urls')),
    path('incident/', include('incident.urls')),
    path('safety-map/', include('safety_map.urls')),
    path('organization/', include('organization.urls')),
    path('admin-panel/', include('admin_panel.urls')),
    
    

    # notifications
    path('notifications/', include('notifications.urls')),
    path('firebase-messaging-sw.js', serve_firebase_sw),

    # REST API
    path('api/', include('accounts.api_urls')),
    path('api/emergency/', include('emergency.api_urls')),
    path('api/tracking/', include('tracking.api_urls')),
    path('api/community/', include('community.api_urls')),
    path('api/guardians/', include('guardians.api_urls')),
    path('api/incident/', include('incident.api_urls')),
    path('api/safety-map/', include('safety_map.api_urls')),
    path(
        'api/notifications/count/',
        __import__('notifications.views', fromlist=['notification_count']).notification_count,
        name='notification-count'
    ),
]





