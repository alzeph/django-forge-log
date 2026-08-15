from __future__ import annotations

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from forge_log.context import get_current_context
from forge_log.middleware import RequestContextMiddleware


@pytest.mark.django_db
def test_middleware_populates_context_for_authenticated_user(django_user_model):
    user = django_user_model.objects.create_user(username="alice", password="x")
    captured = {}

    def get_response(request):
        captured["context"] = get_current_context()
        return "response"

    request = RequestFactory().get("/articles/1/", HTTP_USER_AGENT="pytest-agent")
    request.user = user

    middleware = RequestContextMiddleware(get_response)
    response = middleware(request)

    assert response == "response"
    assert captured["context"].user_id == user.pk
    assert captured["context"].user_repr == "alice"
    assert captured["context"].user_agent == "pytest-agent"
    assert captured["context"].path == "/articles/1/"
    assert captured["context"].method == "GET"


def test_middleware_anonymous_user_is_system_context():
    captured = {}

    def get_response(request):
        captured["context"] = get_current_context()
        return "response"

    request = RequestFactory().get("/")
    request.user = AnonymousUser()

    RequestContextMiddleware(get_response)(request)

    assert captured["context"].user_id is None
    assert captured["context"].user_repr == "anonymous"


@pytest.mark.django_db
def test_context_reflects_user_set_during_view_processing(django_user_model):
    # Reproduit l'authentification DRF (TokenAuthentication, JWT...), qui
    # s'exécute pendant le dispatch de la vue — donc après le passage de ce
    # middleware — et met à jour request.user comme effet de bord. Le
    # contexte doit refléter cette mise à jour, pas un instantané figé pris
    # avant l'exécution de la vue.
    user = django_user_model.objects.create_user(username="bob", password="x")
    captured = {}

    def get_response(request):
        request.user = user  # simule perform_authentication() de DRF
        captured["context"] = get_current_context()
        return "response"

    request = RequestFactory().get("/")
    request.user = AnonymousUser()

    RequestContextMiddleware(get_response)(request)

    assert captured["context"].user_id == user.pk
    assert captured["context"].user_repr == "bob"


def test_context_is_reset_after_request():
    def get_response(request):
        return "response"

    request = RequestFactory().get("/")
    request.user = AnonymousUser()

    RequestContextMiddleware(get_response)(request)

    assert get_current_context().path == ""
