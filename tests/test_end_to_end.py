from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from forge_log.models import ActionLog
from tests.testapp.models import Article


@pytest.mark.django_db
def test_fbv_end_to_end_via_client_and_middleware(client, django_user_model):
    """Client Django réel -> RequestContextMiddleware -> track_action -> writer."""
    user = django_user_model.objects.create_user(username="alice", password="x")
    client.force_login(user)
    article = Article.objects.create(title="Titre", status="draft")

    response = client.post(f"/articles/{article.pk}/update/", {"status": "published"})

    assert response.status_code == 200
    entry = ActionLog.objects.get()
    assert entry.action == "UPDATE"
    assert entry.user_repr == "alice"
    assert entry.endpoint == f"/articles/{article.pk}/update/"
    assert entry.http_method == "POST"
    assert entry.changes["status"]["before"] == "draft"
    assert entry.changes["status"]["after"] == "published"


@pytest.mark.django_db
def test_drf_viewset_create_end_to_end_via_session_auth(django_user_model):
    """APIClient authentifié par session -> AuditViewSetMixin -> writer."""
    user = django_user_model.objects.create_user(username="bob", password="x")
    api = APIClient()
    api.force_login(user)

    response = api.post("/api/articles/", {"title": "Nouveau", "status": "draft"})

    assert response.status_code == 201
    entry = ActionLog.objects.get()
    assert entry.action == "CREATE"
    assert entry.user_repr == "bob"
    assert entry.object_repr == "Nouveau"


@pytest.mark.django_db
def test_drf_authentication_after_middleware_is_still_captured(django_user_model):
    """Régression : l'authentification DRF a lieu pendant le dispatch de la
    vue, après le passage de RequestContextMiddleware (voir StaticTokenAuthentication
    dans tests/views.py, qui n'est pas basée sur la session Django). Avant le
    fix sur la résolution paresseuse du contexte, request.user était figé sur
    AnonymousUser au moment du middleware et l'entrée journalisait
    "anonymous" malgré une requête authentifiée par token.
    """
    user = django_user_model.objects.create_user(username="carol", password="x")
    api = APIClient()

    response = api.post(
        "/api/articles/",
        {"title": "Via token", "status": "draft"},
        HTTP_AUTHORIZATION="Bearer carol",
    )

    assert response.status_code == 201
    entry = ActionLog.objects.get()
    assert entry.user_repr == "carol"
    assert entry.user_id == user.pk


@pytest.mark.django_db
def test_drf_viewset_update_and_destroy_end_to_end(django_user_model):
    user = django_user_model.objects.create_user(username="dave", password="x")
    api = APIClient()
    api.force_login(user)
    article = Article.objects.create(title="Titre", status="draft")
    pk = article.pk

    update_response = api.patch(f"/api/articles/{pk}/", {"status": "published"})
    delete_response = api.delete(f"/api/articles/{pk}/")

    assert update_response.status_code == 200
    assert delete_response.status_code == 204
    actions = list(
        ActionLog.objects.filter(object_id=str(pk))
        .order_by("timestamp")
        .values_list("action", flat=True)
    )
    assert actions == ["UPDATE", "DELETE"]
