from django.apps import AppConfig


class SuscripcionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.suscripciones'
    verbose_name = 'Suscripciones y pagos'

    def ready(self):
        from . import signals  # noqa: F401
