from __future__ import annotations

import time

import pytest

from forge_log.models import ActionLog
from forge_log.recording import record
from tests.testapp.models import Article


@pytest.fixture(autouse=True)
def _threaded_backend(settings):
    settings.FORGE_LOG = {
        "WRITE_BACKEND": "thread",
        "THREAD_FLUSH_INTERVAL": 0.05,
        "THREAD_MAX_BATCH_SIZE": 10,
    }
    from forge_log.writers import reset_writer

    reset_writer()
    yield
    reset_writer()


@pytest.mark.django_db(transaction=True)
def test_threaded_writer_flushes_asynchronously():
    article = Article.objects.create(title="Titre", status="draft")

    record("CREATE", None, article)
    assert ActionLog.objects.count() == 0  # pas encore flushé

    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and ActionLog.objects.count() == 0:
        time.sleep(0.02)

    assert ActionLog.objects.count() == 1
