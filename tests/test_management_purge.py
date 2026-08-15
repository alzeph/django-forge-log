from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from forge_log.models import ActionLog
from forge_log.recording import record
from tests.testapp.models import Article


@pytest.mark.django_db
def test_purge_deletes_old_entries_only():
    article = Article.objects.create(title="Titre", status="draft")
    record("CREATE", None, article)

    old_entry = ActionLog.objects.get()
    ActionLog.objects.filter(pk=old_entry.pk).update(
        timestamp=timezone.now() - timedelta(days=100)
    )

    before = Article.objects.get(pk=article.pk)
    article.status = "published"
    article.save()
    record("UPDATE", before, article)

    call_command("forgelog_purge", "--days", "30")

    assert ActionLog.objects.count() == 1


@pytest.mark.django_db
def test_purge_without_retention_configured_writes_to_stderr():
    from io import StringIO

    stderr = StringIO()
    call_command("forgelog_purge", stderr=stderr)

    assert "Aucune rétention" in stderr.getvalue()
