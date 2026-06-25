from django.urls import path
from . import api_views

urlpatterns = [
    path('trusted-contacts/', api_views.TrustedContactListAPIView.as_view(), name='api-trusted-list'),
    path('trusted-contact/add/', api_views.AddTrustedContactAPIView.as_view(), name='api-trusted-add'),
]
