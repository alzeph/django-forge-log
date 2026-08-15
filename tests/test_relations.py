from __future__ import annotations

import pytest

from forge_log.models import ActionLog
from forge_log.recording import record
from tests.testapp.models import Article


@pytest.mark.django_db
def test_forge_log_entries_reverse_accessor_returns_history():
    article = Article.objects.create(title="a", status="draft")
    record("CREATE", None, article)
    article.status = "published"
    before = Article.objects.get(pk=article.pk)
    record("UPDATE", before, article)

    entries = article.forge_log_entries.all()

    assert entries.count() == 2
    assert list(entries.values_list("action", flat=True).order_by("action")) == [
        "CREATE",
        "UPDATE",
    ]


@pytest.mark.django_db
def test_forge_log_entries_is_scoped_to_the_instance():
    a = Article.objects.create(title="a")
    b = Article.objects.create(title="b")
    record("CREATE", None, a)
    record("CREATE", None, b)

    assert a.forge_log_entries.count() == 1
    assert b.forge_log_entries.count() == 1


@pytest.mark.django_db
def test_deleting_tracked_instance_does_not_delete_its_history():
    # Garantie critique : ForgeLogRelationMixin est délibérément une simple
    # propriété Python, pas un GenericRelation — GenericRelation impose
    # on_delete=CASCADE de façon non configurable (voir GenericRelation.__init__),
    # ce qui supprimerait tout l'historique d'audit en même temps que l'objet.
    article = Article.objects.create(title="a", status="draft")
    record("CREATE", None, article)
    pk = article.pk

    article.delete()

    assert ActionLog.objects.filter(object_id=str(pk)).count() == 1
