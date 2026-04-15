import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FeedbackAnalyserSystem.settings')

app = Celery('FeedbackAnalyserSystem') 

# Загружаем настройки из settings.py, используя префикс CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически ищем файлы tasks.py во всех установленных приложениях Django
app.autodiscover_tasks()