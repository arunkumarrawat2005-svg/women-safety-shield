from django.urls import path
from . import api_views

urlpatterns = [
    path('report/<int:emergency_id>/', api_views.IncidentReportAPIView.as_view(), name='api-incident-report'),
]
