from django.urls import path
from . import views
from .views import DataRecordCreateView

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/records/create/', DataRecordCreateView.as_view(), name='record-create'),
    path('api/v1/integration/feedback/', views.ExternalIntegrationView.as_view(), name='api_integration_feedback'),
]