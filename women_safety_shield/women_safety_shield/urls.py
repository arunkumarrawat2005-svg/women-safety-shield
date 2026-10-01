import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse

def serve_firebase_sw(request):
    file_path = os.path.join(settings.BASE_DIR, 'firebase-messaging-sw.js')
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='application/javascript')
    from django.http import HttpResponse
    return HttpResponse("// FCM SW", content_type='application/javascript')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Web views
    path('', include('accounts.urls')),
    path('emergency/', include('emergency.urls')),
    path('tracking/', include('tracking.urls')),
    path('community/', include('community.urls')),
    path('guardians/', include('local_residents.urls')),  # Backwards compatibility
    path('local-residents/', include('local_residents.urls')),
    path('incident/', include('incident.urls')),
    path('safety-map/', include('safety_map.urls')),
    path('organization/', include('organization.urls')),
    path('organizations/', include('organization.urls')),
    path('admin-panel/', include('admin_panel.urls')),
    path('notifications/', include('notifications.urls')),
    path('verification/', include('verification.urls')),
    path('safe-routes/', include('safe_routes.urls')),
    path('incident-records/', include('incident_records.urls')),

    path('firebase-messaging-sw.js', serve_firebase_sw),

    # REST API Endpoints
    path('api/', include('accounts.api_urls')),
    path('api/emergency/', include('emergency.api_urls')),
    path('api/tracking/', include('tracking.api_urls')),
    path('api/community/', include('community.api_urls')),
    path('api/local-residents/', include('local_residents.api_urls')),
    path('api/guardians/', include('local_residents.api_urls')),  # Backwards compatibility
    path('api/incident/', include('incident.api_urls')),
    path('api/incident-records/', include('incident_records.urls')),
    path('api/safety-map/', include('safety_map.api_urls')),
    path('api/organizations/', include('organization.api_urls')),
    path('api/verification/', include('verification.api_urls')),
    path('api/gov-alerts/', include('gov_alerts.api_urls')),
    path('api/safe-routes/', include('safe_routes.api_urls')),
    path('api/notifications/', include('notifications.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
