from __future__ import annotations

import pytest

from forge_log.writers import _build_writer, get_writer, reset_writer
from forge_log.writers.asyncio_writer import AsyncTaskWriter
from forge_log.writers.celery_writer import CeleryWriter
from forge_log.writers.on_commit import OnCommitWriter
from forge_log.writers.sync import SyncWriter
from forge_log.writers.threaded import ThreadedWriter


@pytest.fixture(autouse=True)
def _cleanup():
    yield
    reset_writer()


@pytest.mark.parametrize(
    "backend,expected_cls",
    [
        ("sync", SyncWriter),
        ("on_commit", OnCommitWriter),
        ("thread", ThreadedWriter),
        ("asyncio", AsyncTaskWriter),
        ("celery", CeleryWriter),
    ],
)
def test_build_writer_selects_expected_backend(settings, backend, expected_cls):
    settings.FORGE_LOG = {"WRITE_BACKEND": backend}
    writer = _build_writer()
    assert isinstance(writer, expected_cls)
    if isinstance(writer, ThreadedWriter):
        writer.stop()


def test_build_writer_invalid_backend_raises(settings):
    settings.FORGE_LOG = {"WRITE_BACKEND": "nope"}
    with pytest.raises(ValueError, match="invalide"):
        _build_writer()


def test_get_writer_is_a_cached_singleton(settings):
    settings.FORGE_LOG = {"WRITE_BACKEND": "sync"}
    reset_writer()

    assert get_writer() is get_writer()


def test_reset_writer_twice_in_a_row_is_a_noop():
    reset_writer()
    reset_writer()
