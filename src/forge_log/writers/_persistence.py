from __future__ import annotations

from typing import TYPE_CHECKING, Any

from forge_log.schemas import ActionLogEntry

if TYPE_CHECKING:
    from forge_log.models import ActionLog


def entry_to_model_kwargs(entry: ActionLogEntry) -> dict[str, Any]:
    from django.contrib.contenttypes.models import ContentType

    content_type = ContentType.objects.get_by_natural_key(
        entry.app_label, entry.model_name
    )

    return {
        "timestamp": entry.timestamp,
        "user_id": entry.user_id,
        "user_repr": entry.user_repr,
        "ip": entry.ip,
        "user_agent": entry.user_agent,
        "action": entry.action,
        "endpoint": entry.endpoint,
        "http_method": entry.http_method,
        "content_type": content_type,
        "object_id": entry.object_id,
        "object_repr": entry.object_repr,
        "changes": {
            name: change.model_dump() for name, change in entry.changes.items()
        },
        "metadata": entry.metadata,
    }


def build_model_instance(entry: ActionLogEntry) -> ActionLog:
    from forge_log.models import ActionLog

    return ActionLog(**entry_to_model_kwargs(entry))
