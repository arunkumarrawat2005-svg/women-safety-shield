from django.urls import path
from . import views

urlpatterns = [
    path('count/', views.notification_count, name='api-notification-count'),
    path('save-token/', views.save_token, name='api-save-fcm-token'),
]
