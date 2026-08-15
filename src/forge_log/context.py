from __future__ import annotations

import contextvars
import ipaddress
from dataclasses import dataclass
from typing import Any, cast


@dataclass(frozen=True)
class RequestContext:
    """Qui/Où d'une requête, propagé via ContextVar (compatible ASGI)."""

    user_id: Any | None = None
    user_repr: str = "system"
    ip: str | None = None
    user_agent: str = ""
    path: str = ""
    method: str = ""


_current_request: contextvars.ContextVar[Any | None] = contextvars.ContextVar(
    "forge_log_request", default=None
)
_current_context: contextvars.ContextVar[RequestContext | None] = (
    contextvars.ContextVar("forge_log_context", default=None)
)


def get_current_context() -> RequestContext:
    """Contexte courant, résolu à la lecture plutôt qu'à l'écriture.

    Si une requête HTTP est active (voir `RequestContextMiddleware`),
    `user_id`/`user_repr` sont recalculés à chaque appel plutôt que figés à
    l'entrée du middleware : l'authentification DRF (`TokenAuthentication`,
    JWT...) s'exécute pendant le dispatch de la vue, après le passage du
    middleware Django — un snapshot pris trop tôt verrait toujours
    `request.user` comme anonyme, même sur une requête authentifiée par un
    mécanisme DRF qui ne passe pas par la session Django.
    """
    request = _current_request.get()
    if request is not None:
        return _context_from_request(request)
    return _current_context.get() or RequestContext()


def set_current_request(request: Any) -> contextvars.Token[Any | None]:
    return _current_request.set(request)


def reset_current_request(token: contextvars.Token[Any | None]) -> None:
    _current_request.reset(token)


def set_current_context(
    context: RequestContext,
) -> contextvars.Token[RequestContext | None]:
    """Injecte un contexte statique explicite (hors requête HTTP)."""
    return _current_context.set(context)


def reset_current_context(token: contextvars.Token[RequestContext | None]) -> None:
    _current_context.reset(token)


def _context_from_request(request: Any) -> RequestContext:
    user = getattr(request, "user", None)
    return RequestContext(
        user_id=(
            user.pk
            if user is not None and getattr(user, "is_authenticated", False)
            else None
        ),
        user_repr=(
            str(user)
            if user is not None and getattr(user, "is_authenticated", False)
            else "anonymous"
        ),
        ip=_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        path=request.path,
        method=request.method or "",
    )


def _client_ip(request: Any) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    candidate = cast(str, forwarded).split(",")[0].strip() if forwarded else None
    candidate = candidate or cast("str | None", request.META.get("REMOTE_ADDR"))
    if not candidate:
        return None
    try:
        # X-Forwarded-For est entièrement contrôlable par le client : une
        # valeur malformée insérée telle quelle ferait planter l'écriture
        # dans GenericIPAddressField sur un backend qui valide le type
        # colonne (ex. `inet` sous PostgreSQL).
        ipaddress.ip_address(candidate)
    except ValueError:
        return None
    return candidate
