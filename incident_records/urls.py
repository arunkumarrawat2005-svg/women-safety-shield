from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path('', views.admin_incident_records_list, name='incident_records_home'),
    # Feature 2: Police Handoff
    path('police-handoff/<int:sos_id>/', views.police_handoff_view, name='police_handoff'),

    # Feature 5: Admin Access & Audit
    path('admin/records/', views.admin_incident_records_list, name='admin_incident_records_list'),
    path('admin/records/<int:record_id>/', views.admin_incident_record_detail, name='admin_incident_record_detail'),

    # Feature 4: Identity Reveal Requests & Proxy Relay
    path('reveal-request/<int:sos_id>/', views.request_identity_reveal_view, name='request_identity_reveal'),
    path('reveal-respond/<int:request_id>/', views.respond_identity_reveal_view, name='respond_identity_reveal'),
    path('proxy-relay/<int:sos_id>/', views.proxy_call_relay_view, name='proxy_call_relay'),

    # APIs
    path('api/breadcrumb/', api_views.RecordBreadcrumbAPIView.as_view(), name='api_record_breadcrumb'),
    path('api/<int:sos_id>/status/', api_views.IncidentRecordStatusAPIView.as_view(), name='api_incident_record_status'),
    path('api/<int:record_id>/unmask/', api_views.AdminUnmaskIdentityAPIView.as_view(), name='api_admin_unmask_identity'),
]
