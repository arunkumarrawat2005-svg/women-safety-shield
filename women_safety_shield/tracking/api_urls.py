from django.urls import path
from . import api_views

urlpatterns = [
    path('update/', api_views.UpdateLocationAPIView.as_view(), name='api-location-update'),
    path('history/', api_views.LocationHistoryAPIView.as_view(), name='api-location-history'),
]
