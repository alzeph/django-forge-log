from __future__ import annotations

import asyncio

from asgiref.sync import sync_to_async

from forge_log.schemas import ActionLogEntry
from forge_log.writers._persistence import build_model_instance


class AsyncTaskWriter:
    """Écrit via asyncio.create_task, pour les vues async (ASGI/Django 4.1+).

    En dehors d'un event loop en cours (appel depuis du code synchrone),
    retombe sur une écriture directe pour ne jamais perdre silencieusement
    une entrée.
    """

    def __init__(self) -> None:
        self._pending: set[asyncio.Task[None]] = set()

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def write(self, entry: ActionLogEntry) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            build_model_instance(entry).save()
            return

        task = loop.create_task(self._save(entry))
        self._pending.add(task)
        task.add_done_callback(self._pending.discard)

    async def wait_pending(self) -> None:
        """À appeler explicitement au shutdown ASGI pour ne pas perdre les
        dernières entrées en cours d'écriture."""
        if self._pending:
            await asyncio.gather(*self._pending, return_exceptions=True)

    @staticmethod
    async def _save(entry: ActionLogEntry) -> None:
        await sync_to_async(build_model_instance(entry).save)()
