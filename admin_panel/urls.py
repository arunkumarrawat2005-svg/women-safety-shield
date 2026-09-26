from django.urls import path
from . import views

urlpatterns = [
    # Organization Governance
    path('organizations/', views.admin_organizations, name='admin_organizations'),
    path('organizations/<int:org_id>/verify/', views.admin_verify_organization, name='admin_verify_organization'),
    path('organizations/<int:org_id>/revoke/', views.admin_revoke_organization, name='admin_revoke_organization'),
    path('organizations/<int:org_id>/delete/', views.admin_delete_organization, name='admin_delete_organization'),

    path('', views.admin_dashboard, name='admin_dashboard'),

    # User Management
    path('users/', views.user_management, name='admin_users'),
    path('users/<int:user_id>/toggle-active/', views.admin_toggle_user_active, name='admin_toggle_user_active'),
    path('users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('users/<int:user_id>/change-role/', views.admin_change_user_role, name='admin_change_user_role'),

    # Emergency Central
    path('emergencies/', views.emergency_management, name='admin_emergencies'),
    path('emergencies/<int:emergency_id>/close/', views.admin_close_emergency, name='admin_close_emergency'),
    path('emergencies/<int:emergency_id>/delete/', views.admin_delete_emergency, name='admin_delete_emergency'),

    # Resident Management & Verifications
    path('residents/', views.resident_management, name='admin_residents'),
    path('resident/<int:resident_id>/verify/', views.verify_resident, name='verify_resident'),
    path('resident/<int:resident_id>/reject/', views.reject_resident, name='reject_resident'),
    path('resident/<int:resident_id>/revoke/', views.revoke_resident, name='revoke_resident'),
    path('resident/<int:resident_id>/delete/', views.admin_delete_resident, name='admin_delete_resident'),
    path('resident/<int:resident_id>/trust-score/', views.admin_update_trust_score, name='admin_update_trust_score'),

    # Backward compatibility aliases for resident verification
    path('guardian/<int:resident_id>/verify/', views.verify_resident, name='verify_guardian'),
    path('residents/<int:resident_id>/verify/', views.verify_resident),
    path('guardians/<int:resident_id>/verify/', views.verify_resident),

    # Safety Reports Moderation
    path('reports/', views.report_management, name='admin_reports'),
    path('reports/<int:report_id>/verify/', views.admin_verify_report, name='admin_verify_report'),
    path('reports/<int:report_id>/delete/', views.admin_delete_report, name='admin_delete_report'),

    # Safety Zones & Hotspots
    path('zones/', views.zone_management, name='admin_zones'),
    path('zones/create/', views.admin_create_zone, name='admin_create_zone'),
    path('zones/<int:zone_id>/delete/', views.admin_delete_zone, name='admin_delete_zone'),

    # Gov Alerts Log
    path('gov-alerts/', views.gov_alerts_log, name='admin_gov_alerts'),

    # Safety Broadcast
    path('broadcast/', views.broadcast_alert, name='admin_broadcast'),

    # User & Resident Verifications Central
    path('verifications/', views.admin_verifications, name='admin_verifications'),
]

