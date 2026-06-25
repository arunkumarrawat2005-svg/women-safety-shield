from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.guardian_register, name='guardian_register'),
    path('profile/', views.guardian_profile, name='guardian_profile'),
    path('toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('update-location/', views.update_location, name='guardian_update_location'),
    path('list/', views.guardian_list, name='guardian_list'),
]
