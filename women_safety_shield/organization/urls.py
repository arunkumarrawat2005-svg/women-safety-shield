from django.urls import path
from . import views
urlpatterns = [path('dashboard/', views.org_dashboard, name='org_dashboard')]
