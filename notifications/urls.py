from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notifications'),
    path('count/', views.notification_count, name='notification_count'),
    path('poll-active-alerts/', views.poll_active_alerts, name='poll_active_alerts'),
    path('<int:pk>/read/', views.mark_read, name='mark_read'),
    path('read-all/', views.mark_all_read, name='mark_all_read'),
]
