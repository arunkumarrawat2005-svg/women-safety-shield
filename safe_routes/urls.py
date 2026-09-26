from django.urls import path
from . import views

urlpatterns = [
    path('', views.compare_routes_view, name='safe_routes_home'),
    path('compare/', views.compare_routes_view, name='safe_routes_compare'),
]
