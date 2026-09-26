from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.resident_register, name='resident_register'),
    path('profile/', views.resident_profile, name='resident_profile'),
    path('toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('update-location/', views.update_location, name='resident_update_location'),
    path('list/', views.resident_list, name='resident_list'),
    path('safe-escort/request/', views.request_safe_escort, name='request_safe_escort'),
    path('safe-escort/<int:pk>/respond/', views.respond_safe_escort, name='respond_safe_escort'),

    # Backward compatibility URL names
    path('legacy/register/', views.resident_register, name='guardian_register'),
    path('legacy/profile/', views.resident_profile, name='guardian_profile'),
    path('legacy/update-location/', views.update_location, name='guardian_update_location'),
    path('legacy/list/', views.resident_list, name='guardian_list'),
]
