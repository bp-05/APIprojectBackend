from django.apps import AppConfig


class SubjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subjects'

    def ready(self):
        # Import signals so they register on app startup
        from . import signals  # noqa: F401
