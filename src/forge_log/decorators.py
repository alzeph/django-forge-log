from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, TypeVar

from asgiref.sync import iscoroutinefunction, sync_to_async
from django.db.models import Model

from forge_log.conf import app_settings
from forge_log.recording import record

F = TypeVar("F", bound=Callable[..., Any])

_HTTP_METHOD_TO_ACTION = {
    "POST": "CREATE",
    "PUT": "UPDATE",
    "PATCH": "UPDATE",
    "DELETE": "DELETE",
}


def _default_get_instance(model: type[Model]) -> Callable[..., Model | None]:
    pk_name = model._meta.pk.name

    def getter(*args: Any, **kwargs: Any) -> Model | None:
        pk = kwargs.get("pk", kwargs.get(pk_name))
        if pk is None:
            return None
        return model._default_manager.filter(pk=pk).first()

    return getter


def _find_request(args: tuple[Any, ...]) -> Any | None:
    for value in args:
        if hasattr(value, "method") and hasattr(value, "path"):
            return value
    return None


def _resolve_action(action: str | None, args: tuple[Any, ...]) -> str:
    if action is not None:
        return action
    request = _find_request(args)
    if request is None:
        return "CUSTOM"
    return _HTTP_METHOD_TO_ACTION.get(request.method, "CUSTOM")


def track_action(
    model: type[Model],
    *,
    get_instance: Callable[..., Model | None] | None = None,
    fields: list[str] | None = None,
    action: str | None = None,
) -> Callable[[F], F]:
    """Journalise dans ActionLog une FBV ou une méthode CBV touchant `model`.

    Sans `get_instance`, l'instance est recherchée via le PK présent dans les
    kwargs de la vue (`pk`, ou le nom du champ clé primaire) — le cas courant
    `/resource/<pk>/`. Pour les créations (pas de PK dans l'URL avant
    l'exécution de la vue), fournissez `get_instance` explicitement, ou
    préférez `forge_log.drf.AuditViewSetMixin` sur un ViewSet DRF, qui capture
    nativement les créations via `perform_create`.

    `get_instance` reçoit les mêmes *args/**kwargs que la vue décorée et est
    appelé deux fois (avant et après l'exécution de la vue) pour obtenir
    l'état avant/après.

    Détecte automatiquement une vue `async def` (`asgiref.sync.iscoroutinefunction`)
    et bascule `get_instance`/le calcul du diff/l'écriture sur `sync_to_async`,
    exécutés dans le thread de l'executor plutôt que sur l'event loop. Avec
    `WRITE_BACKEND="asyncio"`, cela signifie qu'aucune boucle asyncio n'est
    "en cours" dans ce thread : l'écriture retombe sur le chemin synchrone de
    `AsyncTaskWriter` plutôt que sur `asyncio.create_task()`. Toujours
    correct, mais sans le gain de perf attendu de ce backend — préférez
    `thread` ou `celery` pour des vues suivies async à fort trafic.
    """
    instance_getter = get_instance or _default_get_instance(model)

    def decorator(view_func: F) -> F:
        if iscoroutinefunction(view_func):
            return _wrap_async(view_func, model, instance_getter, fields, action)
        return _wrap_sync(view_func, model, instance_getter, fields, action)

    return decorator


def _wrap_sync(
    view_func: F,
    model: type[Model],
    instance_getter: Callable[..., Model | None],
    fields: list[str] | None,
    action: str | None,
) -> F:
    @functools.wraps(view_func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not app_settings.ENABLED:
            return view_func(*args, **kwargs)

        before = instance_getter(*args, **kwargs)
        response = view_func(*args, **kwargs)
        after = instance_getter(*args, **kwargs)

        resolved_action = _resolve_action(action, args)
        record(resolved_action, before, after, model=model, fields=fields)
        return response

    return wrapper  # type: ignore[return-value]


def _wrap_async(
    view_func: F,
    model: type[Model],
    instance_getter: Callable[..., Model | None],
    fields: list[str] | None,
    action: str | None,
) -> F:
    @functools.wraps(view_func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not app_settings.ENABLED:
            return await view_func(*args, **kwargs)

        before = await sync_to_async(instance_getter)(*args, **kwargs)
        response = await view_func(*args, **kwargs)
        after = await sync_to_async(instance_getter)(*args, **kwargs)

        resolved_action = _resolve_action(action, args)
        await sync_to_async(record)(
            resolved_action, before, after, model=model, fields=fields
        )
        return response

    return wrapper  # type: ignore[return-value]
