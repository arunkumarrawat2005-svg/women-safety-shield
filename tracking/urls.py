from django.urls import path
from . import views

urlpatterns = [
    path('', views.live_map, name='tracking_home'),
    path('live/', views.live_map, name='live_map'),
    path('history/', views.location_history, name='location_history'),
    path('heartbeat/', views.heartbeat_location, name='tracking_heartbeat'),
]
