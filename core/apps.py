"""Configuração do app core."""

from django.apps import AppConfig

class CoreConfig(AppConfig):
    """Configuração padrão do app core."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        """Registra os signals ao iniciar o app."""
        import core.signals  # noqa: F401
