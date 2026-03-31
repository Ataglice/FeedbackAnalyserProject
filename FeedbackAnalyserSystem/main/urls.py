from django.urls import path
from . import views

urlpatterns = [
    path('main/', views.dashboard_view, name="dashboard"),
    path('feedback_feed/', views.feedback_view, name="feedback_feed"),
    path('config/', views.config, name="config")
]
