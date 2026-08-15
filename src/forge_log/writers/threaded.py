from __future__ import annotations

import queue
import threading
import time

from django.db import connections

from forge_log.conf import app_settings
from forge_log.schemas import ActionLogEntry
from forge_log.writers._persistence import build_model_instance


class ThreadedWriter:
    """File en mémoire consommée par un unique thread démon persistant.

    `write()` fait un `put_nowait` et rend la main immédiatement : le coût
    perf sur la vue suivie est celui d'un enqueue, pas d'une écriture SQL.
    Le thread vide la file par lots (bulk_create) toutes les
    `THREAD_FLUSH_INTERVAL` secondes ou dès `THREAD_MAX_BATCH_SIZE` entrées.

    Limite assumée : les entrées en attente de flush sont perdues si le
    process est tué avant écriture (fenêtre ~THREAD_FLUSH_INTERVAL). Pour
    une garantie de durabilité stricte, utiliser le backend "on_commit" ou
    "celery" à la place.
    """

    def __init__(self) -> None:
        self._queue: queue.Queue[ActionLogEntry] = queue.Queue(
            maxsize=app_settings.THREAD_MAX_QUEUE_SIZE
        )
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="forge-log-writer"
        )
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return
        self._stop_event.set()
        self._thread.join(timeout=5)
        self._thread = None

    def write(self, entry: ActionLogEntry) -> None:
        try:
            self._queue.put_nowait(entry)
        except queue.Full:
            pass  # ne jamais bloquer la requête ; l'entrée est perdue

    def _run(self) -> None:
        interval = app_settings.THREAD_FLUSH_INTERVAL
        batch_size = app_settings.THREAD_MAX_BATCH_SIZE
        while not self._stop_event.is_set():
            self._flush(self._collect(interval, batch_size))
        self._flush(self._collect(0, batch_size))  # dernier drain avant arrêt

    def _collect(self, timeout: float, batch_size: int) -> list[ActionLogEntry]:
        batch: list[ActionLogEntry] = []
        deadline = time.monotonic() + timeout
        while len(batch) < batch_size:
            remaining = deadline - time.monotonic()
            if remaining <= 0 and batch:
                break
            try:
                batch.append(self._queue.get(timeout=max(remaining, 0.001)))
            except queue.Empty:
                break
        return batch

    def _flush(self, batch: list[ActionLogEntry]) -> None:
        if not batch:
            return
        from forge_log.models import ActionLog

        try:
            ActionLog.objects.bulk_create(build_model_instance(e) for e in batch)
        finally:
            connections.close_all()
