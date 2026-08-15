from __future__ import annotations

import re
from typing import Any

from django.db.models import Model

from forge_log.conf import app_settings
from forge_log.schemas import FieldChange


def _compiled_patterns(patterns: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def _forge_log_meta(instance: Model) -> type[Any] | None:
    return getattr(type(instance), "ForgeLogMeta", None)


def _model_excluded_fields(instance: Model) -> set[str]:
    meta = _forge_log_meta(instance)
    return set(getattr(meta, "excluded_fields", []))


def _model_masked_fields(instance: Model) -> set[str]:
    meta = _forge_log_meta(instance)
    return set(getattr(meta, "masked_fields", []))


def _snapshot(instance: Model, fields: list[str] | None) -> dict[str, Any]:
    tracked = fields or [f.name for f in instance._meta.concrete_fields]
    return {name: getattr(instance, name) for name in tracked}


def _serialize(value: Any) -> Any:
    from django.db.models.fields.files import FieldFile

    if isinstance(value, FieldFile):
        return value.name or None
    if isinstance(value, Model):
        return str(value.pk)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def compute_diff(
    before: Model | None,
    after: Model,
    fields: list[str] | None = None,
) -> dict[str, FieldChange]:
    """Compare deux instances et retourne les champs modifiés.

    Les champs listés dans `MASKED_FIELDS` (config ou `ForgeLogMeta`) sont
    toujours signalés comme modifiés mais sans exposer les valeurs. Les
    champs `EXCLUDED_FIELDS` n'apparaissent jamais dans le diff.
    """
    excluded_patterns = _compiled_patterns(app_settings.EXCLUDED_FIELDS)
    masked = _model_masked_fields(after) | set(app_settings.MASKED_FIELDS)
    excluded = _model_excluded_fields(after)

    before_values = _snapshot(before, fields) if before is not None else {}
    after_values = _snapshot(after, fields)

    changes: dict[str, FieldChange] = {}
    for name in sorted(set(before_values) | set(after_values)):
        before_val = before_values.get(name)
        after_val = after_values.get(name)
        if before_val == after_val:
            continue

        is_masked = name in masked
        is_excluded = not is_masked and (
            name in excluded or any(p.search(name) for p in excluded_patterns)
        )
        if is_excluded:
            continue

        if is_masked:
            changes[name] = FieldChange(masked=True)
        else:
            changes[name] = FieldChange(
                before=_serialize(before_val), after=_serialize(after_val)
            )

    return changes
