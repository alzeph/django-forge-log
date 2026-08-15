from __future__ import annotations

from typing import Any

from django.db.models import Model
from django.utils import timezone

from forge_log.conf import app_settings
from forge_log.context import RequestContext, get_current_context
from forge_log.diff import compute_diff
from forge_log.schemas import ActionLogEntry
from forge_log.signals import action_logged


def record(
    action: str,
    before: Model | None,
    after: Model | None,
    *,
    model: type[Model] | None = None,
    fields: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    context: RequestContext | None = None,
    allow_without_instance: bool = False,
) -> None:
    """Construit une ActionLogEntry et la remet au writer configuré.

    Point d'entrée unique utilisé par le décorateur `track_action`, le mixin
    DRF, l'intégration Admin et l'intégration `django-signals-all` (bulk).
    """
    if not app_settings.ENABLED:
        return

    reference = after or before
    if reference is None and not allow_without_instance:
        return

    resolved_model = model or (type(reference) if reference is not None else None)
    if resolved_model is None:
        return

    diff = compute_diff(before, after, fields=fields) if after is not None else {}
    if action == "UPDATE" and before is not None and after is not None and not diff:
        return

    ctx = context or get_current_context()
    entry = ActionLogEntry(
        timestamp=timezone.now(),
        user_id=ctx.user_id,
        user_repr=ctx.user_repr,
        ip=ctx.ip,
        user_agent=ctx.user_agent,
        endpoint=ctx.path,
        http_method=ctx.method,
        action=action,
        app_label=resolved_model._meta.app_label,
        model_name=resolved_model._meta.model_name or "",
        object_id=str(reference.pk) if reference is not None else None,
        object_repr=(
            str(reference)
            if reference is not None
            else f"{resolved_model._meta.verbose_name}"
        ),
        changes=diff,
        metadata=metadata or {},
    )

    from forge_log.writers import get_writer

    action_logged.send(sender=resolved_model, entry=entry)
    get_writer().write(entry)
