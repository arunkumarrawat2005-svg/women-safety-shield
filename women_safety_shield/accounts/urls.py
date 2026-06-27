from django.urls import path
from . import views
from .views import save_fcm_token
from django.conf import settings


urlpatterns = [
    path('', views.home_view, name='home'),
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('sos/', views.sos_view, name='sos'),
    path("save-token/", save_fcm_token, name="save_token"),
]
