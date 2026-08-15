from __future__ import annotations

from forge_log.schemas import ActionLogEntry
from forge_log.writers._persistence import build_model_instance


class SyncWriter:
    """Écriture immédiate et bloquante. Le plus sûr, le plus coûteux en perf."""

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def write(self, entry: ActionLogEntry) -> None:
        build_model_instance(entry).save()
