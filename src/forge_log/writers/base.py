from __future__ import annotations

from typing import Protocol

from forge_log.schemas import ActionLogEntry


class Writer(Protocol):
    """Backend d'écriture d'une ActionLogEntry vers la table ActionLog."""

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def write(self, entry: ActionLogEntry) -> None: ...
