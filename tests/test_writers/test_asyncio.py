from __future__ import annotations

import asyncio

import pytest
from django.utils import timezone

from forge_log.models import ActionLog
from forge_log.schemas import ActionLogEntry
from forge_log.writers.asyncio_writer import AsyncTaskWriter
from tests.testapp.models import Article


def _entry(object_id: str = "1") -> ActionLogEntry:
    return ActionLogEntry(
        timestamp=timezone.now(),
        action="CREATE",
        app_label="testapp",
        model_name="article",
        object_id=object_id,
        object_repr="Titre",
    )


@pytest.mark.django_db
def test_write_outside_event_loop_falls_back_to_sync_save():
    article = Article.objects.create(title="Titre", status="draft")

    AsyncTaskWriter().write(_entry(str(article.pk)))

    assert ActionLog.objects.count() == 1


def test_write_inside_event_loop_schedules_a_task(monkeypatch):
    # Isolé de la DB : on fait tourner l'ordonnancement asyncio réel
    # (create_task/wait_pending) sans toucher au thread-safety de sqlite
    # en mémoire, qui casse l'accès depuis le thread de sync_to_async.
    saved = []

    class FakeInstance:
        def save(self) -> None:
            saved.append(True)

    monkeypatch.setattr(
        "forge_log.writers.asyncio_writer.build_model_instance",
        lambda entry: FakeInstance(),
    )

    writer = AsyncTaskWriter()

    async def scenario() -> None:
        writer.write(_entry())
        assert len(writer._pending) == 1
        await writer.wait_pending()

    asyncio.run(scenario())

    assert saved == [True]
    assert writer._pending == set()
