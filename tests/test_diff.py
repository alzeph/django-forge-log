from __future__ import annotations

from forge_log.diff import compute_diff
from tests.testapp.models import Article


def test_no_before_reports_all_fields_as_after_only():
    after = Article(pk=1, title="Titre", status="draft")
    diff = compute_diff(None, after)
    assert diff["title"].after == "Titre"
    assert diff["title"].before is None


def test_only_changed_fields_are_reported():
    before = Article(pk=1, title="Titre", status="draft")
    after = Article(pk=1, title="Titre", status="published")
    diff = compute_diff(before, after)
    assert list(diff) == ["status"]
    assert diff["status"].before == "draft"
    assert diff["status"].after == "published"


def test_excluded_field_never_appears():
    before = Article(pk=1, title="Titre", internal_note="a")
    after = Article(pk=1, title="Titre", internal_note="b")
    diff = compute_diff(before, after)
    assert "internal_note" not in diff


def test_masked_field_hides_values(settings):
    settings.FORGE_LOG = {"MASKED_FIELDS": ["title"]}
    before = Article(pk=1, title="a", status="draft")
    after = Article(pk=1, title="b", status="draft")
    diff = compute_diff(before, after)
    assert diff["title"].masked is True
    assert diff["title"].before is None
    assert diff["title"].after is None


def test_fields_argument_restricts_comparison():
    before = Article(pk=1, title="a", status="draft")
    after = Article(pk=1, title="b", status="published")
    diff = compute_diff(before, after, fields=["status"])
    assert list(diff) == ["status"]
