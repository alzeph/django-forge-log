from __future__ import annotations

import pytest

from forge_log.conf import app_settings


def test_default_values():
    assert app_settings.ENABLED is True
    assert app_settings.WRITE_BACKEND == "sync"  # défini dans tests/settings.py


def test_override_settings_reloads(settings):
    settings.FORGE_LOG = {"WRITE_BACKEND": "on_commit"}
    assert app_settings.WRITE_BACKEND == "on_commit"


def test_unknown_setting_raises():
    with pytest.raises(AttributeError):
        _ = app_settings.DOES_NOT_EXIST


def test_unrelated_setting_change_does_not_reload(settings):
    # Force le cache, puis modifie un réglage Django sans rapport : la
    # branche `if setting == SETTINGS_KEY` ne doit pas se déclencher.
    assert app_settings.ENABLED is True
    settings.DEBUG = not settings.DEBUG
    assert app_settings.ENABLED is True
