from django.urls import path
from . import views

urlpatterns = [
    # Public Directory & Safe Havens
    path('', views.org_list, name='org_list'),
    path('directory/', views.org_list, name='org_directory'),
    path('<int:org_id>/', views.org_detail, name='org_detail'),
    path('<int:org_id>/join/', views.org_join, name='org_join'),

    # Registration & Onboarding
    path('register/', views.org_register, name='org_register'),

    # Institutional Operations Command Center
    path('dashboard/', views.org_dashboard, name='org_dashboard'),
    path('dashboard/profile/', views.update_org_profile, name='update_org_profile'),
    path('volunteers/add/', views.add_org_volunteer, name='add_org_volunteer'),
    path('volunteers/<int:volunteer_id>/approve/', views.approve_volunteer, name='approve_org_volunteer'),
    path('volunteers/<int:volunteer_id>/reject/', views.reject_volunteer, name='reject_org_volunteer'),
    path('volunteers/<int:volunteer_id>/toggle/', views.toggle_volunteer_availability, name='toggle_org_volunteer'),
    path('responses/<int:response_id>/assign/', views.assign_org_responder, name='assign_org_responder'),
]
