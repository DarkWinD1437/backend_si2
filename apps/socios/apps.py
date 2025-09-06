# apps.py
from django.apps import AppConfig

class SociosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.socios'
    verbose_name = 'Gestión de Socios'
    
    def ready(self):
        import apps.socios.signals