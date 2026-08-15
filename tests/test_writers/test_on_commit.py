from __future__ import annotations

import pytest

from forge_log.models import ActionLog
from forge_log.recording import record
from tests.testapp.models import Article


@pytest.fixture(autouse=True)
def _on_commit_backend(settings):
    settings.FORGE_LOG = {"WRITE_BACKEND": "on_commit"}
    from forge_log.writers import reset_writer

    reset_writer()
    yield
    reset_writer()


@pytest.mark.django_db
def test_entry_written_only_after_commit(django_capture_on_commit_callbacks):
    # django_db (non transactionnel) enveloppe le test dans un atomic() implicite,
    # exactement comme TestCase : on_commit() reste en attente au lieu de
    # s'exécuter immédiatement, ce que capture précisément ce test.
    article = Article.objects.create(title="Titre", status="draft")

    with django_capture_on_commit_callbacks(execute=True):
        record("CREATE", None, article)

    assert ActionLog.objects.count() == 1


@pytest.mark.django_db
def test_entry_not_written_without_commit(django_capture_on_commit_callbacks):
    article = Article.objects.create(title="Titre", status="draft")

    with django_capture_on_commit_callbacks(execute=False):
        record("CREATE", None, article)

    assert ActionLog.objects.count() == 0
