from __future__ import annotations

import ipaddress
from collections.abc import Callable
from typing import cast

from django.http import HttpRequest, HttpResponse

from forge_log.context import RequestContext, reset_current_context, set_current_context


def _client_ip(request: HttpRequest) -> str | None:
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


class RequestContextMiddleware:
    """Capture Qui/Où (user, IP, User-Agent, route) dans un ContextVar.

    Basé sur contextvars plutôt que threading.local pour rester valide sous
    ASGI, où plusieurs requêtes partagent le même thread/event loop.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = getattr(request, "user", None)
        context = RequestContext(
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
        token = set_current_context(context)
        try:
            return self.get_response(request)
        finally:
            reset_current_context(token)
