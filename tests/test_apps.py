from __future__ import annotations

from django.apps import apps

from forge_log import writers


def test_ready_builds_writer_when_enabled(settings):
    settings.FORGE_LOG = {"ENABLED": True, "WRITE_BACKEND": "sync"}
    writers.reset_writer()

    apps.get_app_config("forge_log").ready()

    assert writers._writer is not None
    writers.reset_writer()


def test_ready_skips_writer_when_disabled(settings):
    settings.FORGE_LOG = {"ENABLED": False}
    writers.reset_writer()

    apps.get_app_config("forge_log").ready()

    assert writers._writer is None
