from django.urls import path
from . import views

urlpatterns = [
    path('', views.safety_map_view, name='safety_map'),
    path('report/', views.submit_report, name='submit_safety_report'),
]
