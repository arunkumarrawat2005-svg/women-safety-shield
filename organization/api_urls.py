from django.urls import path
from . import api_views

urlpatterns = [
    path('register/', api_views.RegisterOrganizationAPIView.as_view(), name='api-org-register'),
    path('<int:org_id>/volunteers/add/', api_views.AddOrgVolunteerAPIView.as_view(), name='api-org-volunteer-add'),
    path('respond/<int:sos_id>/acknowledge/', api_views.AcknowledgeOrgResponseAPIView.as_view(), name='api-org-acknowledge'),
    path('<int:org_id>/dashboard-alerts/', api_views.OrgDashboardAlertsAPIView.as_view(), name='api-org-dashboard-alerts'),
]
