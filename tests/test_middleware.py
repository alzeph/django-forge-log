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


def test_forwarded_for_header_takes_precedence_over_remote_addr():
    captured = {}

    def get_response(request):
        captured["context"] = get_current_context()
        return "response"

    request = RequestFactory().get(
        "/", HTTP_X_FORWARDED_FOR="203.0.113.5, 10.0.0.1", REMOTE_ADDR="127.0.0.1"
    )
    request.user = AnonymousUser()

    RequestContextMiddleware(get_response)(request)

    assert captured["context"].ip == "203.0.113.5"


def test_context_is_reset_after_request():
    def get_response(request):
        return "response"

    request = RequestFactory().get("/")
    request.user = AnonymousUser()

    RequestContextMiddleware(get_response)(request)

    assert get_current_context().path == ""
