from __future__ import annotations

import contextvars
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RequestContext:
    """Qui/Où d'une requête, propagé via ContextVar (compatible ASGI)."""

    user_id: Any | None = None
    user_repr: str = "system"
    ip: str | None = None
    user_agent: str = ""
    path: str = ""
    method: str = ""


_current_context: contextvars.ContextVar[RequestContext | None] = (
    contextvars.ContextVar("forge_log_context", default=None)
)


def get_current_context() -> RequestContext:
    return _current_context.get() or RequestContext()


def set_current_context(
    context: RequestContext,
) -> contextvars.Token[RequestContext | None]:
    return _current_context.set(context)


def reset_current_context(token: contextvars.Token[RequestContext | None]) -> None:
    _current_context.reset(token)
