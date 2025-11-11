from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # Import signal handlers (post_migrate) to auto-cargar scripts/populate.json si existe
        from . import signals  # noqa: F401
        # Intento oportunista al iniciar la app (idempotente y tolerante a errores)
        try:
            # Ejecuta solo si DB y tablas están listas; si no, post_migrate lo hará
            signals._load_populate_json()
        except Exception:
            # Silencioso: post_migrate hará el populate cuando corresponda
            pass
