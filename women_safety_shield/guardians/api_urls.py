from django.urls import path
from . import api_views

urlpatterns = [
    path('register/', api_views.RegisterGuardianAPIView.as_view(), name='api-guardian-register'),
    path('nearby/', api_views.NearbyGuardiansAPIView.as_view(), name='api-guardian-nearby'),
]
