from __future__ import annotations

import asyncio

import pytest

from forge_log.decorators import track_action
from forge_log.models import ActionLog
from tests.testapp.models import Article


@pytest.mark.django_db(transaction=True)
def test_async_view_logs_diff():
    article = Article.objects.create(title="Titre", status="draft")

    @track_action(Article)
    async def update_status(request, pk):
        obj = await Article.objects.aget(pk=pk)
        obj.status = "published"
        await obj.asave()
        return "ok"

    class FakeRequest:
        method = "PATCH"
        path = f"/articles/{article.pk}/"

    async def scenario() -> str:
        return await update_status(FakeRequest(), pk=article.pk)

    result = asyncio.run(scenario())

    assert result == "ok"
    entry = ActionLog.objects.get()
    assert entry.action == "UPDATE"
    assert entry.changes["status"]["before"] == "draft"
    assert entry.changes["status"]["after"] == "published"


@pytest.mark.django_db(transaction=True)
def test_async_view_with_no_change_does_not_log():
    article = Article.objects.create(title="Titre", status="draft")

    @track_action(Article)
    async def noop(request, pk):
        return "ok"

    class FakeRequest:
        method = "PATCH"
        path = "/x/"

    asyncio.run(noop(FakeRequest(), pk=article.pk))

    assert ActionLog.objects.count() == 0


def test_async_view_disabled_setting_skips_logging(settings):
    settings.FORGE_LOG = {"ENABLED": False}

    @track_action(Article)
    async def update_status(pk):
        return "skipped"

    result = asyncio.run(update_status(pk=1))

    assert result == "skipped"
