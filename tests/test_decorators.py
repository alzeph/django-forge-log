from __future__ import annotations

import pytest

from forge_log.decorators import track_action
from forge_log.models import ActionLog
from tests.testapp.models import Article


@pytest.mark.django_db
def test_update_view_logs_diff():
    article = Article.objects.create(title="Titre", status="draft")

    @track_action(Article)
    def update_status(request, pk):
        obj = Article.objects.get(pk=pk)
        obj.status = "published"
        obj.save()
        return "ok"

    class FakeRequest:
        method = "PATCH"
        path = f"/articles/{article.pk}/"

    result = update_status(FakeRequest(), pk=article.pk)

    assert result == "ok"
    entry = ActionLog.objects.get()
    assert entry.action == "UPDATE"
    assert entry.object_id == str(article.pk)
    assert entry.changes["status"]["before"] == "draft"
    assert entry.changes["status"]["after"] == "published"


@pytest.mark.django_db
def test_view_with_no_change_does_not_log():
    article = Article.objects.create(title="Titre", status="draft")

    @track_action(Article)
    def noop(request, pk):
        return "ok"

    class FakeRequest:
        method = "PATCH"
        path = "/x/"

    noop(FakeRequest(), pk=article.pk)

    assert ActionLog.objects.count() == 0


@pytest.mark.django_db
def test_explicit_get_instance_and_action():
    article = Article.objects.create(title="Titre", status="draft")

    @track_action(
        Article, get_instance=lambda **kw: Article.objects.filter(pk=kw["pk"]).first()
    )
    def delete_article(pk):
        Article.objects.filter(pk=pk).delete()

    delete_article(pk=article.pk)

    entry = ActionLog.objects.get()
    assert entry.action == "CUSTOM"  # pas de request détectable dans les args
    assert entry.object_id == str(article.pk)


@pytest.mark.django_db
def test_disabled_setting_skips_logging(settings):
    settings.FORGE_LOG = {"ENABLED": False}
    article = Article.objects.create(title="Titre", status="draft")

    @track_action(Article)
    def update_status(pk):
        Article.objects.filter(pk=pk).update(status="published")

    update_status(pk=article.pk)

    assert ActionLog.objects.count() == 0
