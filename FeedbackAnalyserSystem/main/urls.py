from django.urls import path
from . import views

urlpatterns = [
    path('main/', views.dashboard_view, name="dashboard"),
    path('feedback_feed/', views.feedback_view, name="feedback_feed"),
    path('config/', views.config, name="config"),
    path('config/delete-user/<int:user_id>/', views.delete_employee, name='delete_employee'),
    path('config/edit-user/<int:user_id>/', views.edit_employee, name='edit_employee'),
    path('config/dictionary/', views.dictionary_view, name='dictionary'),
    path('config/dictionary/delete/<int:pk>/', views.delete_anchor, name='delete_anchor'),
    path('config/dictionary/edit/<int:pk>/', views.edit_anchor, name='edit_anchor'),
    path('config/dictionary/import/', views.import_anchors, name='import_anchors'),
    path('profile/', views.profile_view, name='profile'),
    path('feedback/<int:feedback_id>/override/', views.override_sentiment, name='override_sentiment'),
    path('settings/notifications/', views.notifications_settings_view, name='notifications'),
]
