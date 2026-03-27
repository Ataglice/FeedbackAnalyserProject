from django.urls import path
from . import views

urlpatterns = [
    path('main/', views.dashboard_view, name="dashboard")
]
