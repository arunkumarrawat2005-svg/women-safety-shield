from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.incident_list, name='incident_list'),
    path('<int:emergency_id>/timeline/', views.incident_timeline, name='incident_timeline'),
    path('<int:emergency_id>/report/', views.incident_report, name='incident_report'),
]
