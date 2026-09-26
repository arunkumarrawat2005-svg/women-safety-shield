from django.urls import path
from . import views

urlpatterns = [
    path('', views.trusted_contacts, name='community_home'),
    path('trusted-contacts/', views.trusted_contacts, name='trusted_contacts'),
    path('trusted-contacts/add/', views.add_trusted_contact, name='add_trusted_contact'),
    path('trusted-contacts/<int:pk>/remove/', views.remove_trusted_contact, name='remove_trusted_contact'),
    path('trusted-contacts/<int:pk>/toggle-primary/', views.toggle_primary_contact, name='toggle_primary_contact'),
    path('trusted-contacts/<int:pk>/test/', views.test_trusted_contact, name='test_trusted_contact'),
    path('trusted-contacts/<int:pk>/edit/', views.edit_trusted_contact, name='edit_trusted_contact'),
    path('trusted-contacts/checkin/', views.send_safe_checkin, name='send_safe_checkin'),
]
