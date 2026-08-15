from __future__ import annotations

import sys

import pytest

from forge_log import signals_integration
from forge_log.models import ActionLog
from tests.testapp.models import Article


@pytest.fixture(autouse=True)
def _connect_signals():
    signals_integration.connect()


def test_connect_is_a_noop_when_django_signals_all_is_unavailable(monkeypatch):
    # Une entrée à None dans sys.modules force un ImportError à l'import
    # suivant, ce qui simule l'extra `[signals]` non installé.
    monkeypatch.setitem(sys.modules, "django_signals_all.signals", None)

    signals_integration.connect()  # ne doit pas lever


@pytest.mark.django_db
def test_bulk_create_signal_logs_each_object():
    from django_signals_all.signals import post_bulk_create

    articles = [Article(title="a", status="draft"), Article(title="b", status="draft")]
    post_bulk_create.send(sender=Article, objects=articles, using="default")

    assert ActionLog.objects.filter(action="BULK_CREATE").count() == 2


@pytest.mark.django_db
def test_bulk_update_signal_logs_aggregated_entry():
    from django_signals_all.signals import post_bulk_update

    post_bulk_update.send(
        sender=Article,
        updated_ids=[1, 2, 3],
        update_kwargs={"status": "archived"},
        using="default",
    )

    entry = ActionLog.objects.get(action="BULK_UPDATE")
    assert entry.metadata["count"] == 3
    assert entry.object_id is None


@pytest.mark.django_db
def test_bulk_model_update_signal_logs_per_instance():
    from django_signals_all.signals import post_bulk_model_update

    article = Article.objects.create(title="a", status="draft")
    article.status = "archived"

    post_bulk_model_update.send(
        sender=Article,
        updated_instances=[article],
        fields_updated=["status"],
        using="default",
    )

    entry = ActionLog.objects.get(action="BULK_UPDATE")
    assert entry.object_id == str(article.pk)
