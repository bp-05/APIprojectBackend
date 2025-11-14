from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # Import signal handlers (post_migrate) to auto-cargar scripts/populate.json si existe
        from . import signals  # noqa: F401
