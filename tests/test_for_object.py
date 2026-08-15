from __future__ import annotations

import pytest

from forge_log.models import ActionLog
from forge_log.recording import record
from tests.testapp.models import Article


@pytest.mark.django_db
def test_for_object_returns_only_entries_for_that_instance():
    a = Article.objects.create(title="a")
    b = Article.objects.create(title="b")
    record("CREATE", None, a)
    record("CREATE", None, b)

    entries = ActionLog.objects.for_object(a)

    assert entries.count() == 1
    assert entries.get().object_id == str(a.pk)


@pytest.mark.django_db
def test_for_object_is_chainable_with_further_filtering():
    article = Article.objects.create(title="a", status="draft")
    record("CREATE", None, article)
    article.status = "published"
    before = Article.objects.get(pk=article.pk)
    record("UPDATE", before, article)

    entries = ActionLog.objects.for_object(article).filter(action="UPDATE")

    assert entries.count() == 1


@pytest.mark.django_db
def test_for_object_returns_empty_for_untracked_instance():
    article = Article.objects.create(title="a")

    assert ActionLog.objects.for_object(article).count() == 0
