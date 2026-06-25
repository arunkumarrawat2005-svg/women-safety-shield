from django.urls import path
from . import views

urlpatterns = [
    path('live/', views.live_map, name='live_map'),
    path('history/', views.location_history, name='location_history'),
]
