from django.urls import path
from . import views
from .views import save_fcm_token


urlpatterns = [
    path('', views.home_view, name='home'),
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),

    # Direct convenient aliases
    path('login/', views.login_view, name='login_direct'),
    path('register/', views.register_view, name='register_direct'),
    path('logout/', views.logout_view, name='logout_direct'),
    path('favicon.ico', views.favicon_view, name='favicon'),

    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('how-it-works/', views.how_it_works_view, name='how_it_works'),
    path('permissions/', views.permission_model_view, name='permission_model'),
    path('terms/', views.terms_view, name='terms'),

    path("save-token/", save_fcm_token, name="save_token"),
    path('download/apk/', views.download_apk_view, name='download_apk'),
    path('manifest.json', views.manifest_view, name='manifest_json'),
    path('sw.js', views.service_worker_view, name='service_worker'),
]
