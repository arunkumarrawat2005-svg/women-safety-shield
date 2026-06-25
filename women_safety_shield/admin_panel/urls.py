from django.urls import path
from . import views
urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('guardian/<int:guardian_id>/verify/', views.verify_guardian, name='verify_guardian'),
    path('users/', views.user_management, name='admin_users'),
]
