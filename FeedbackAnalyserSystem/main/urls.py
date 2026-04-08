from django.urls import path
from . import views

urlpatterns = [
    path('main/', views.dashboard_view, name="dashboard"),
    path('feedback_feed/', views.feedback_view, name="feedback_feed"),
    path('config/', views.config, name="config"),
    path('config/delete-user/<int:user_id>/', views.delete_employee, name='delete_employee'),
    path('config/edit-user/<int:user_id>/', views.edit_employee, name='edit_employee'),
    path('config/dictionary/', views.dictionary_view, name='dictionary')

]
