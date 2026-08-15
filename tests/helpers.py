from __future__ import annotations

from typing import Any

from django.utils import timezone

from forge_log.schemas import ActionLogEntry


def make_entry(**overrides: Any) -> ActionLogEntry:
    defaults: dict[str, Any] = dict(
        timestamp=timezone.now(),
        action="CREATE",
        app_label="testapp",
        model_name="article",
        object_id="1",
        object_repr="Titre",
    )
    defaults.update(overrides)
    return ActionLogEntry(**defaults)
