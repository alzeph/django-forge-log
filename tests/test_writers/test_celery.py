from __future__ import annotations

import pytest
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from forge_log.models import ActionLog
from forge_log.schemas import ActionLogEntry
from forge_log.writers import celery_writer
from tests.testapp.models import Article


@pytest.mark.django_db
def test_celery_writer_serializes_payload_for_dispatch(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        celery_writer.write_entry_task,
        "delay",
        lambda payload: captured.update(payload),
    )

    article = Article.objects.create(title="Titre", status="draft")
    entry = ActionLogEntry(
        timestamp=timezone.now(),
        action="CREATE",
        app_label="testapp",
        model_name="article",
        object_id=str(article.pk),
        object_repr="Titre",
    )

    celery_writer.CeleryWriter().write(entry)

    assert captured["object_repr"] == "Titre"
    assert isinstance(captured["timestamp"], str)
    assert captured["content_type_id"] == ContentType.objects.get_for_model(Article).pk


@pytest.mark.django_db
def test_write_entry_task_persists_an_action_log():
    ct = ContentType.objects.get_for_model(Article)
    payload = {
        "timestamp": timezone.now().isoformat(),
        "user_id": None,
        "user_repr": "system",
        "ip": None,
        "user_agent": "",
        "action": "CREATE",
        "endpoint": "",
        "http_method": "",
        "content_type_id": ct.pk,
        "object_id": "1",
        "object_repr": "Titre",
        "changes": {},
        "metadata": {},
    }

    # Appeler la tâche directement (sans .delay()) l'exécute en synchrone,
    # sans nécessiter de broker Celery configuré.
    celery_writer.write_entry_task(payload)

    assert ActionLog.objects.count() == 1
