from django.urls import path
from . import api_views
from . import views

urlpatterns = [
    path('heartbeat/', views.heartbeat_location, name='api-location-heartbeat'),
    path('update/', api_views.UpdateLocationAPIView.as_view(), name='api-location-update'),
    path('history/', api_views.LocationHistoryAPIView.as_view(), name='api-location-history'),
]
