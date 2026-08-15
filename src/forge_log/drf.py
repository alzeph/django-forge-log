from __future__ import annotations

import copy

try:
    from rest_framework.serializers import BaseSerializer
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "forge_log.drf nécessite djangorestframework : installez l'extra "
        "`django-forge-log[drf]`."
    ) from exc

from django.db.models import Model

from forge_log.recording import record


class AuditViewSetMixin:
    """Journalise create/update/destroy pour un DRF ViewSet, sans configuration.

    À combiner avec un ModelViewSet (ou tout générique DRF exposant
    perform_create/perform_update/perform_destroy) :

        class ArticleViewSet(AuditViewSetMixin, ModelViewSet):
            queryset = Article.objects.all()
            serializer_class = ArticleSerializer

    Contrairement à `track_action`, capture correctement les créations
    (l'instance créée est disponible via `serializer.instance` juste après
    `perform_create`, sans avoir besoin de la retrouver par PK dans l'URL).
    """

    forge_log_fields: list[str] | None = None

    def perform_create(self, serializer: BaseSerializer) -> None:
        super().perform_create(serializer)  # type: ignore[misc]
        record("CREATE", None, serializer.instance, fields=self.forge_log_fields)

    def perform_update(self, serializer: BaseSerializer) -> None:
        before = _refetch(serializer.instance)
        super().perform_update(serializer)  # type: ignore[misc]
        record("UPDATE", before, serializer.instance, fields=self.forge_log_fields)

    def perform_destroy(self, instance: Model) -> None:
        # Model.delete() met instance.pk à None en place : capturer un
        # instantané avant, pour ne pas journaliser un object_id vide.
        snapshot = copy.copy(instance)
        super().perform_destroy(instance)  # type: ignore[misc]
        record("DELETE", snapshot, None, fields=self.forge_log_fields)


def _refetch(instance: Model) -> Model | None:
    return type(instance)._default_manager.filter(pk=instance.pk).first()
