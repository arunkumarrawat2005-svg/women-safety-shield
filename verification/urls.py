from django.urls import path
from . import views

urlpatterns = [
    path('', views.verification_status, name='verification_home'),
    # Citizen Verification Flow
    path('status/', views.verification_status, name='verification_status'),
    path('submit/', views.verification_status, name='verification_submit'),

    # Admin Verification Panel
    path('admin/', views.admin_verification_dashboard, name='admin_verification_dashboard'),
    path('admin/<int:req_id>/action/', views.admin_verification_action, name='admin_verification_action'),

    # Government / Police Verification Portal
    path('police-portal/', views.police_portal_view, name='police_portal'),
    path('police-portal/log-access/', views.police_log_access, name='police_log_access'),
]
