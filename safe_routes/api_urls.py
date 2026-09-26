from django.urls import path
from . import api_views

urlpatterns = [
    path('compare/', api_views.SafeRoutesCompareAPIView.as_view(), name='api-safe-routes-compare'),
    path('segment-score/', api_views.SegmentScoreAPIView.as_view(), name='api-safe-routes-segment-score'),
]
