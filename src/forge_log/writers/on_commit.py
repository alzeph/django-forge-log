from __future__ import annotations

from django.db import transaction

from forge_log.schemas import ActionLogEntry
from forge_log.writers._persistence import build_model_instance


class OnCommitWriter:
    """Écrit via transaction.on_commit : jamais loggé si la transaction rollback.

    Reste bloquant pour la requête (le callback s'exécute avant que la
    réponse ne parte), contrairement à ThreadedWriter/AsyncTaskWriter.
    """

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def write(self, entry: ActionLogEntry) -> None:
        transaction.on_commit(lambda: build_model_instance(entry).save())
