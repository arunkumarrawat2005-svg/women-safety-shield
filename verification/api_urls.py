from django.urls import path
from . import api_views

urlpatterns = [
    path('submit/', api_views.SubmitVerificationAPIView.as_view(), name='api-verification-submit'),
    path('status/', api_views.VerificationStatusAPIView.as_view(), name='api-verification-status'),
    path('review/<int:id>/', api_views.ReviewVerificationAPIView.as_view(), name='api-verification-review'),
]
