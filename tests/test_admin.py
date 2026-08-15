from __future__ import annotations

import pytest
from django.contrib import admin as django_admin

from forge_log.admin import ActionLogAdmin, AuditModelAdminMixin
from forge_log.models import ActionLog
from tests.testapp.models import Article


@pytest.fixture
def action_log_admin():
    return ActionLogAdmin(ActionLog, django_admin.site)


def test_action_log_admin_is_fully_read_only(action_log_admin):
    assert action_log_admin.has_add_permission(None) is False
    assert action_log_admin.has_change_permission(None) is False
    assert action_log_admin.has_delete_permission(None) is False


class ArticleAdmin(AuditModelAdminMixin, django_admin.ModelAdmin):
    pass


@pytest.mark.django_db
def test_audit_mixin_logs_creation_and_update():
    site = django_admin.AdminSite()
    admin_instance = ArticleAdmin(Article, site)

    article = Article(title="Titre", status="draft")
    admin_instance.save_model(request=None, obj=article, form=None, change=False)
    assert ActionLog.objects.filter(action="CREATE").count() == 1

    article.status = "published"
    admin_instance.save_model(request=None, obj=article, form=None, change=True)
    entry = ActionLog.objects.get(action="UPDATE")
    assert entry.changes["status"]["after"] == "published"


@pytest.mark.django_db
def test_audit_mixin_logs_delete():
    site = django_admin.AdminSite()
    admin_instance = ArticleAdmin(Article, site)
    article = Article.objects.create(title="Titre", status="draft")

    admin_instance.delete_model(request=None, obj=article)

    assert ActionLog.objects.get().action == "DELETE"
