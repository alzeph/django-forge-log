from typing import Any, cast

from django.conf import settings
from django.test.signals import setting_changed

SETTINGS_KEY = "FORGE_LOG"

DEFAULTS: dict[str, Any] = {
    "ENABLED": True,
    # "sync" | "on_commit" | "thread" | "asyncio" | "celery"
    "WRITE_BACKEND": "thread",
    "EXCLUDED_FIELDS": [
        r".*secret.*",
        r".*token.*",
        r".*_key$",
        r"credit_card",
        r"ssn",
    ],
    "MASKED_FIELDS": ["password"],
    "RETENTION_DAYS": None,
    "THREAD_FLUSH_INTERVAL": 0.2,
    "THREAD_MAX_BATCH_SIZE": 50,
    "THREAD_MAX_QUEUE_SIZE": 10_000,
}


class Settings:
    """Accès paresseux au dict FORGE_LOG, invalidé par override_settings."""

    def __init__(self, defaults: dict[str, Any]) -> None:
        self.defaults = defaults
        self._cached_attrs: set[str] = set()

    @property
    def user_settings(self) -> dict[str, Any]:
        return cast(dict[str, Any], getattr(settings, SETTINGS_KEY, {}))

    def __getattr__(self, attr: str) -> Any:
        if attr not in self.defaults:
            raise AttributeError(f"Réglage {SETTINGS_KEY} invalide : {attr!r}")
        try:
            value = self.user_settings[attr]
        except KeyError:
            value = self.defaults[attr]
        self._cached_attrs.add(attr)
        setattr(self, attr, value)
        return value

    def reload(self) -> None:
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()


app_settings = Settings(DEFAULTS)


def _reload_settings(*, setting: str, **kwargs: Any) -> None:
    if setting == SETTINGS_KEY:
        app_settings.reload()
        from forge_log.writers import reset_writer

        reset_writer()


setting_changed.connect(_reload_settings)
