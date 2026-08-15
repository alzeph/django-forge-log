from django.apps import AppConfig


class ForgeLogConfig(AppConfig):
    name = "forge_log"
    verbose_name = "Forge Log"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from forge_log import signals_integration
        from forge_log.conf import app_settings
        from forge_log.writers import get_writer

        signals_integration.connect()
        if app_settings.ENABLED:
            get_writer()
