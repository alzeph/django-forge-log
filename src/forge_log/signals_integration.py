from __future__ import annotations

from typing import Any

from forge_log.recording import record


def connect() -> None:
    """Branche les receivers sur django_signals_all si l'extra est installé.

    Sans l'extra `django-forge-log[signals]`, no-op silencieux : les
    mutations bulk (.update(), bulk_create(), bulk_update()) ne sont
    simplement pas journalisées automatiquement.
    """
    try:
        from django_signals_all.signals import (
            post_bulk_create,
            post_bulk_model_update,
            post_bulk_update,
        )
    except ImportError:
        return

    post_bulk_create.connect(_on_bulk_create, dispatch_uid="forge_log_bulk_create")
    post_bulk_update.connect(_on_bulk_update, dispatch_uid="forge_log_bulk_update")
    post_bulk_model_update.connect(
        _on_bulk_model_update, dispatch_uid="forge_log_bulk_model_update"
    )


def _on_bulk_create(
    sender: type, objects: list[Any], using: str, **kwargs: Any
) -> None:
    for obj in objects:
        record("BULK_CREATE", None, obj, model=sender)


def _on_bulk_update(
    sender: type,
    updated_ids: list[Any],
    update_kwargs: dict[str, Any],
    using: str,
    **kwargs: Any,
) -> None:
    # .filter(...).update(...) ne charge pas les instances : une entrée
    # agrégée est journalisée plutôt qu'une entrée par objet.
    record(
        "BULK_UPDATE",
        None,
        None,
        model=sender,
        allow_without_instance=True,
        metadata={
            "updated_ids": [str(pk) for pk in updated_ids],
            "update_kwargs": {k: str(v) for k, v in update_kwargs.items()},
            "count": len(updated_ids),
        },
    )


def _on_bulk_model_update(
    sender: type,
    updated_instances: list[Any],
    fields_updated: list[str],
    using: str,
    **kwargs: Any,
) -> None:
    for instance in updated_instances:
        record("BULK_UPDATE", None, instance, model=sender, fields=fields_updated)
