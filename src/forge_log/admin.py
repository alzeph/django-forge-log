from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.db.models import Model

from forge_log.models import ActionLog
from forge_log.recording import record


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Lecture seule : la table d'audit ne doit pas être modifiable depuis l'Admin."""

    list_display = (
        "timestamp",
        "action",
        "user_repr",
        "content_type",
        "object_repr",
        "endpoint",
    )
    list_filter = ("action", "content_type")
    search_fields = ("user_repr", "object_repr", "endpoint")
    date_hierarchy = "timestamp"
    readonly_fields = [f.name for f in ActionLog._meta.fields]

    def has_add_permission(self, request: Any) -> bool:
        return False

    def has_change_permission(self, request: Any, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: Any, obj: Any = None) -> bool:
        return False


class AuditModelAdminMixin:
    """Redirige save_model/delete_model vers ActionLog, en plus du LogEntry natif.

        class ArticleAdmin(AuditModelAdminMixin, admin.ModelAdmin):
            forge_log_fields = None  # ou une liste de champs à suivre

    Unifie l'Admin et les vues suivies par `track_action`/`AuditViewSetMixin`
    dans la même table `ActionLog`.
    """

    forge_log_fields: list[str] | None = None

    def save_model(self, request: Any, obj: Model, form: Any, change: bool) -> None:
        before = (
            type(obj)._default_manager.filter(pk=obj.pk).first() if change else None
        )
        super().save_model(request, obj, form, change)  # type: ignore[misc]
        record(
            "UPDATE" if change else "CREATE",
            before,
            obj,
            fields=self.forge_log_fields,
        )

    def delete_model(self, request: Any, obj: Model) -> None:
        super().delete_model(request, obj)  # type: ignore[misc]
        record("DELETE", obj, None, fields=self.forge_log_fields)
