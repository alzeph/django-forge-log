from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from forge_log.models import ActionLog
from forge_log.recording import record
from tests.testapp.models import Article


@pytest.mark.django_db
def test_decimal_field_diff_does_not_crash_on_write():
    before = Article(pk=1, title="a", price=Decimal("9.99"))
    after = Article.objects.create(title="a", price=Decimal("12.50"))

    record("UPDATE", before, after)

    entry = ActionLog.objects.get()
    assert entry.changes["price"]["before"] == "9.99"
    assert entry.changes["price"]["after"] == "12.50"


@pytest.mark.django_db
def test_uuid_field_diff_does_not_crash_on_write():
    ref_a, ref_b = uuid.uuid4(), uuid.uuid4()
    before = Article(pk=1, title="a", external_ref=ref_a)
    after = Article.objects.create(title="a", external_ref=ref_b)

    record("UPDATE", before, after)

    entry = ActionLog.objects.get()
    assert entry.changes["external_ref"]["before"] == str(ref_a)
    assert entry.changes["external_ref"]["after"] == str(ref_b)
