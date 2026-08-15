from __future__ import annotations

import pytest

from forge_log.writers import reset_writer


@pytest.fixture(autouse=True)
def _reset_writer_cache():
    reset_writer()
    yield
    reset_writer()
