from __future__ import annotations

from forge_log.context import (
    RequestContext,
    get_current_context,
    reset_current_context,
    set_current_context,
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
