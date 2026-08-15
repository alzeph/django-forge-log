from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class FieldChange(BaseModel):
    """Un champ modifié : valeurs avant/après, ou masqué si sensible."""

    model_config = ConfigDict(frozen=True)

    before: Any = None
    after: Any = None
    masked: bool = False


class ActionLogEntry(BaseModel):
    """Représentation stricte d'une entrée d'audit avant persistance."""

    model_config = ConfigDict(frozen=True)

    timestamp: datetime
    user_id: Any | None = None
    user_repr: str = "system"
    ip: str | None = None
    user_agent: str = ""
    endpoint: str = ""
    http_method: str = ""
    action: str
    app_label: str
    model_name: str
    object_id: str | None = None
    object_repr: str = ""
    changes: dict[str, FieldChange] = {}
    metadata: dict[str, Any] = {}
