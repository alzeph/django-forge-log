from __future__ import annotations

from functools import cache
from typing import Any

from django.db.models import CharField, Model
from django.utils import timezone

from forge_log.conf import app_settings
from forge_log.context import RequestContext, get_current_context
from forge_log.diff import compute_diff
from forge_log.schemas import ActionLogEntry
from forge_log.signals import action_logged


@cache
def _max_length(field_name: str) -> int:
    # Import différé : ActionLog ne doit pas être importé au chargement du
    # module (avant que le registre d'apps Django ne soit prêt).
    from forge_log.models import ActionLog

    field = ActionLog._meta.get_field(field_name)
    assert isinstance(field, CharField)
    assert field.max_length is not None
    return field.max_length


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
    object_repr = (
        str(reference)
        if reference is not None
        else str(resolved_model._meta.verbose_name)
    )
    entry = ActionLogEntry(
        timestamp=timezone.now(),
        user_id=ctx.user_id,
        # Troncature défensive : ces valeurs alimentent des CharField, et un
        # __str__ de modèle un peu verbeux ou une route longue ferait
        # planter l'écriture sur un backend qui valide la longueur de
        # colonne (ex. varchar(n) strict sous PostgreSQL) au lieu de la
        # tronquer silencieusement comme SQLite.
        user_repr=ctx.user_repr[: _max_length("user_repr")],
        ip=ctx.ip,
        user_agent=ctx.user_agent,
        endpoint=ctx.path[: _max_length("endpoint")],
        http_method=ctx.method[: _max_length("http_method")],
        action=action[: _max_length("action")],
        app_label=resolved_model._meta.app_label,
        model_name=resolved_model._meta.model_name or "",
        object_id=(
            str(reference.pk)[: _max_length("object_id")]
            if reference is not None
            else None
        ),
        object_repr=object_repr[: _max_length("object_repr")],
        changes=diff,
        metadata=metadata or {},
    )

    from forge_log.writers import get_writer

    action_logged.send(sender=resolved_model, entry=entry)
    get_writer().write(entry)
