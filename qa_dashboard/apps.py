from django.apps import AppConfig


class QaDashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'qa_dashboard'

    def ready(self):
        import qa_dashboard.signals
