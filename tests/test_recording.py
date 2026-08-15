from __future__ import annotations

import pytest

from forge_log.models import ActionLog
from forge_log.recording import record
from tests.testapp.models import Article


@pytest.mark.django_db
def test_disabled_globally_skips_logging(settings):
    settings.FORGE_LOG = {"ENABLED": False}
    article = Article.objects.create(title="Titre", status="draft")

    record("CREATE", None, article)

    assert ActionLog.objects.count() == 0


@pytest.mark.django_db
def test_no_instance_and_no_opt_in_skips_logging():
    record("BULK_UPDATE", None, None)

    assert ActionLog.objects.count() == 0


@pytest.mark.django_db
def test_no_instance_no_model_even_with_opt_in_skips_logging():
    # allow_without_instance=True mais ni before/after ni model : impossible
    # de résoudre le modèle concerné, donc rien à journaliser.
    record("BULK_UPDATE", None, None, allow_without_instance=True)

    assert ActionLog.objects.count() == 0


@pytest.mark.django_db
def test_opt_in_without_instance_but_with_model_logs_aggregated_entry():
    record(
        "BULK_UPDATE",
        None,
        None,
        model=Article,
        allow_without_instance=True,
        metadata={"count": 3},
    )

    entry = ActionLog.objects.get()
    assert entry.object_id is None
    assert entry.metadata == {"count": 3}


@pytest.mark.django_db
def test_long_object_repr_is_truncated_instead_of_crashing_on_write():
    article = Article.objects.create(title="x" * 500)

    record("CREATE", None, article)

    entry = ActionLog.objects.get()
    max_length = ActionLog._meta.get_field("object_repr").max_length
    assert len(entry.object_repr) == max_length


@pytest.mark.django_db
def test_long_custom_action_is_truncated_instead_of_crashing_on_write():
    article = Article.objects.create(title="a")

    record("X" * 100, None, article)

    entry = ActionLog.objects.get()
    max_length = ActionLog._meta.get_field("action").max_length
    assert len(entry.action) == max_length
