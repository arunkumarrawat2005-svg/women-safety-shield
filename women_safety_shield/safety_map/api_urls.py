from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.SafetyMapAPIView.as_view(), name='api-safety-map'),
    path('report/', api_views.SubmitSafetyReportAPIView.as_view(), name='api-safety-report'),
]
