from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import api_views

urlpatterns = [
    path('register/', api_views.RegisterAPIView.as_view(), name='api-register'),
    path('login/', api_views.LoginAPIView.as_view(), name='api-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', api_views.ProfileAPIView.as_view(), name='api-profile'),
    path('users/', api_views.UserListAPIView.as_view(), name='api-users'),
]
