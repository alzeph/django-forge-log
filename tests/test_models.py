from __future__ import annotations

import pytest
from django.utils import timezone

from forge_log.models import ActionLog


@pytest.mark.django_db
def test_str_includes_action_and_object_repr():
    entry = ActionLog.objects.create(
        timestamp=timezone.now(),
        action=ActionLog.Action.CREATE,
        object_repr="Titre",
    )

    assert "CREATE" in str(entry)
    assert "Titre" in str(entry)
