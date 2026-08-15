from __future__ import annotations

from forge_log.conf import app_settings
from forge_log.writers.base import Writer

_writer: Writer | None = None

_BACKENDS = ("sync", "on_commit", "thread", "asyncio", "celery")


def get_writer() -> Writer:
    global _writer
    if _writer is None:
        _writer = _build_writer()
        _writer.start()
    return _writer


def reset_writer() -> None:
    """Force la reconstruction du writer (ex: après override_settings)."""
    global _writer
    if _writer is not None:
        _writer.stop()
    _writer = None


def _build_writer() -> Writer:
    backend = app_settings.WRITE_BACKEND
    if backend == "sync":
        from forge_log.writers.sync import SyncWriter

        return SyncWriter()
    if backend == "on_commit":
        from forge_log.writers.on_commit import OnCommitWriter

        return OnCommitWriter()
    if backend == "thread":
        from forge_log.writers.threaded import ThreadedWriter

        return ThreadedWriter()
    if backend == "asyncio":
        from forge_log.writers.asyncio_writer import AsyncTaskWriter

        return AsyncTaskWriter()
    if backend == "celery":
        from forge_log.writers.celery_writer import CeleryWriter

        return CeleryWriter()
    raise ValueError(
        f"FORGE_LOG['WRITE_BACKEND'] invalide : {backend!r} "
        f"(attendu : {', '.join(_BACKENDS)})"
    )
