from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ActionLog(models.Model):
    """Table d'audit centrale : Qui/Quoi/Quand/Où/Diff pour toute mutation suivie."""

    class Action(models.TextChoices):
        CREATE = "CREATE", "Création"
        UPDATE = "UPDATE", "Modification"
        DELETE = "DELETE", "Suppression"
        BULK_CREATE = "BULK_CREATE", "Création en masse"
        BULK_UPDATE = "BULK_UPDATE", "Modification en masse"
        CUSTOM = "CUSTOM", "Action personnalisée"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(db_index=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    user_repr = models.CharField(max_length=255, default="system")
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")

    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)

    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    object_id = models.CharField(max_length=255, null=True, blank=True)
    object_repr = models.CharField(max_length=255, blank=True, default="")
    content_object = GenericForeignKey("content_type", "object_id")

    endpoint = models.CharField(max_length=255, blank=True, default="")
    http_method = models.CharField(max_length=10, blank=True, default="")

    changes = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["content_type", "object_id", "-timestamp"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.object_repr} @ {self.timestamp:%Y-%m-%d %H:%M:%S}"
