from __future__ import annotations

import pytest

from forge_log.models import ActionLog
from forge_log.recording import record
from tests.testapp.models import Article


@pytest.mark.django_db
def test_sync_writer_persists_immediately():
    article = Article.objects.create(title="Titre", status="draft")
    record("CREATE", None, article)

    assert ActionLog.objects.count() == 1
    entry = ActionLog.objects.get()
    assert entry.object_repr == "Titre"
    assert entry.content_type.model == "article"
