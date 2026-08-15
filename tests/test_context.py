from __future__ import annotations

from django.http import HttpRequest
from django.test import RequestFactory

from forge_log.context import (
    RequestContext,
    _client_ip,
    get_current_context,
    reset_current_context,
    reset_current_request,
    set_current_context,
    set_current_request,
)


def test_default_context_is_system():
    assert get_current_context() == RequestContext()


def test_set_and_reset_context():
    context = RequestContext(user_id=1, user_repr="alice")
    token = set_current_context(context)
    try:
        assert get_current_context() == context
    finally:
        reset_current_context(token)
    assert get_current_context() == RequestContext()


def test_set_and_reset_request():
    request = RequestFactory().get("/articles/1/", HTTP_USER_AGENT="pytest-agent")
    token = set_current_request(request)
    try:
        context = get_current_context()
        assert context.path == "/articles/1/"
        assert context.user_agent == "pytest-agent"
    finally:
        reset_current_request(token)
    assert get_current_context() == RequestContext()


def test_request_takes_precedence_over_static_context():
    static_token = set_current_context(RequestContext(user_repr="static"))
    request = RequestFactory().get("/from-request/")
    request_token = set_current_request(request)
    try:
        assert get_current_context().path == "/from-request/"
    finally:
        reset_current_request(request_token)
        reset_current_context(static_token)


def test_forwarded_for_header_takes_precedence_over_remote_addr():
    request = RequestFactory().get(
        "/", HTTP_X_FORWARDED_FOR="203.0.113.5, 10.0.0.1", REMOTE_ADDR="127.0.0.1"
    )

    assert _client_ip(request) == "203.0.113.5"


def test_malformed_forwarded_for_is_rejected_instead_of_stored_raw():
    # X-Forwarded-For est entièrement contrôlable par le client : une valeur
    # malformée insérée telle quelle dans GenericIPAddressField ferait
    # planter l'écriture sous PostgreSQL (colonne "inet" stricte).
    request = RequestFactory().get(
        "/", HTTP_X_FORWARDED_FOR="'; DROP TABLE forge_log_actionlog;--"
    )

    assert _client_ip(request) is None


def test_valid_ipv6_forwarded_for_is_kept():
    request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="2001:db8::1")

    assert _client_ip(request) == "2001:db8::1"


def test_client_ip_returns_none_without_any_ip_source():
    request = HttpRequest()  # META vide : ni X-Forwarded-For, ni REMOTE_ADDR

    assert _client_ip(request) is None
