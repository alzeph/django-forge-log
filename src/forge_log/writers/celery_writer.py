from __future__ import annotations

from typing import Any

try:
    from celery import shared_task
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Le backend FORGE_LOG['WRITE_BACKEND'] = 'celery' nécessite Celery : "
        "installez l'extra `django-forge-log[celery]`."
    ) from exc

from django.utils.dateparse import parse_datetime

from forge_log.schemas import ActionLogEntry
from forge_log.writers._persistence import entry_to_model_kwargs


@shared_task(name="forge_log.write_entry")  # type: ignore[untyped-decorator]
def write_entry_task(payload: dict[str, Any]) -> None:
    from forge_log.models import ActionLog

    content_type_id = payload.pop("content_type_id")
    payload["timestamp"] = parse_datetime(payload["timestamp"])
    ActionLog.objects.create(content_type_id=content_type_id, **payload)


class CeleryWriter:
    """Dispatch total hors du cycle requête/réponse via une tâche Celery.

    Le plus robuste sous forte charge (nécessite un broker configuré côté
    projet utilisateur) : l'écriture ne dépend plus du tout du process web.
    """

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def write(self, entry: ActionLogEntry) -> None:
        payload = entry_to_model_kwargs(entry)
        content_type = payload.pop("content_type")
        payload["content_type_id"] = content_type.pk
        payload["timestamp"] = entry.timestamp.isoformat()
        write_entry_task.delay(payload)
