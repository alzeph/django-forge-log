from __future__ import annotations

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from forge_log.context import reset_current_request, set_current_request


class RequestContextMiddleware:
    """Rend la requête courante disponible pour la résolution du contexte
    Qui/Où (voir `forge_log.context.get_current_context`).

    Stocke une référence à `request` — pas un snapshot figé — dans un
    ContextVar, compatible ASGI (plusieurs requêtes partagent le même
    thread/event loop). La résolution paresseuse (au moment de la lecture,
    pas de l'écriture) permet de capturer correctement un utilisateur
    authentifié par DRF après le passage de ce middleware.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        token = set_current_request(request)
        try:
            return self.get_response(request)
        finally:
            reset_current_request(token)
