from django.urls import path
from . import api_views

urlpatterns = [
    path('register/', api_views.RegisterLocalResidentAPIView.as_view(), name='api-resident-register'),
    path('nearby/', api_views.NearbyLocalResidentsAPIView.as_view(), name='api-resident-nearby'),
    path('respond/<int:sos_id>/acknowledge/', api_views.AcknowledgeLocalResidentResponseAPIView.as_view(), name='api-resident-acknowledge'),

    # Backward compatibility URL names
    path('legacy/register/', api_views.RegisterLocalResidentAPIView.as_view(), name='api-guardian-register'),
    path('legacy/nearby/', api_views.NearbyLocalResidentsAPIView.as_view(), name='api-guardian-nearby'),
]
