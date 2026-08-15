from __future__ import annotations

import time

import pytest

from forge_log.models import ActionLog
from forge_log.recording import record
from forge_log.writers.threaded import ThreadedWriter
from tests.helpers import make_entry
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


def test_start_is_idempotent():
    writer = ThreadedWriter()
    writer.start()
    first_thread = writer._thread
    writer.start()  # ne doit pas relancer un second thread
    assert writer._thread is first_thread
    writer.stop()


def test_stop_without_start_is_a_noop():
    writer = ThreadedWriter()
    writer.stop()  # jamais démarré : ne doit pas lever
    assert writer._thread is None


def test_write_drops_entry_silently_when_queue_is_full(settings):
    settings.FORGE_LOG = {"THREAD_MAX_QUEUE_SIZE": 1}
    writer = ThreadedWriter()  # pas de start() : personne ne vide la file

    writer.write(make_entry())
    writer.write(make_entry())  # ne doit pas lever malgré la file pleine

    assert writer._queue.qsize() == 1


def test_collect_stops_at_batch_size_without_waiting_for_timeout():
    writer = ThreadedWriter()
    for _ in range(5):
        writer._queue.put_nowait(make_entry())

    batch = writer._collect(timeout=1, batch_size=3)

    assert len(batch) == 3


def test_collect_breaks_when_deadline_passed_with_a_partial_batch(monkeypatch):
    from forge_log.writers import threaded as threaded_module

    # deadline = 100+0 = 100 ; 1er contrôle (batch vide) = 100-100 = 0 -> pas de
    # break ; après avoir dépilé l'unique entrée, 2e contrôle = 100-105 = -5
    # avec batch non vide -> break avant même le timeout de get().
    clock = iter([100.0, 100.0, 105.0])
    monkeypatch.setattr(threaded_module.time, "monotonic", lambda: next(clock))

    writer = ThreadedWriter()
    writer._queue.put_nowait(make_entry())

    batch = writer._collect(timeout=0, batch_size=10)

    assert len(batch) == 1
