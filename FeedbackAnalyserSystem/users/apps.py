from django.apps import AppConfig
import sys

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users' 

    def ready(self):
        ignore_commands = ['makemigrations', 'migrate', 'collectstatic', 'createsuperuser', 'shell']

        is_terminal_command = any(cmd in sys.argv for cmd in ignore_commands)

        if not is_terminal_command:
            try:
                from .views import get_analyzer
                
                print(">>> Предзагрузка AI-моделей в память сервера... <<<")
                get_analyzer() 
                print(">>> AI-модели успешно загружены и готовы к работе! <<<")
            except ImportError:
                pass
