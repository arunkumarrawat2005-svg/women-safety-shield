from django.urls import path
from . import views

urlpatterns = [
    path('trusted-contacts/', views.trusted_contacts, name='trusted_contacts'),
    path('trusted-contacts/add/', views.add_trusted_contact, name='add_trusted_contact'),
    path('trusted-contacts/<int:pk>/remove/', views.remove_trusted_contact, name='remove_trusted_contact'),
]
