from django.urls import path
from . import api_views

urlpatterns = [
    path('create/', api_views.CreateEmergencyAPIView.as_view(), name='api-emergency-create'),
    path('status/', api_views.EmergencyStatusAPIView.as_view(), name='api-emergency-status'),
    path('<int:pk>/accept/', api_views.AcceptEmergencyAPIView.as_view(), name='api-emergency-accept'),
    path('<int:pk>/close/', api_views.CloseEmergencyAPIView.as_view(), name='api-emergency-close'),
]
