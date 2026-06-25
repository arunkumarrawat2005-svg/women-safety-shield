from django.urls import path
from . import views

urlpatterns = [
    path('sos/', views.sos_view, name='sos'),
    path('sos/trigger/', views.trigger_sos, name='trigger_sos'),
    path('list/', views.emergency_list, name='emergency_list'),
    path('<int:pk>/track/', views.emergency_track, name='emergency_track'),
    path('<int:pk>/close/', views.close_emergency, name='close_emergency'),
    path('<int:pk>/accept/', views.accept_emergency, name='accept_emergency'),
    path('guardian/', views.guardian_emergencies, name='guardian_emergencies'),
]
