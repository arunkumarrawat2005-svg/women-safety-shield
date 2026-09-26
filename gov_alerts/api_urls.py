from django.urls import path
from . import api_views

urlpatterns = [
    path('notify/<int:sos_id>/', api_views.TriggerGovAlertAPIView.as_view(), name='api-gov-alert-notify'),
    path('<int:sos_id>/status/', api_views.GovAlertStatusAPIView.as_view(), name='api-gov-alert-status'),
]
