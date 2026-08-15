from __future__ import annotations

import pytest
from rest_framework import serializers
from rest_framework.viewsets import ModelViewSet

from forge_log.drf import AuditViewSetMixin
from forge_log.models import ActionLog
from tests.testapp.models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "status"]


class ArticleViewSet(AuditViewSetMixin, ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer


@pytest.mark.django_db
def test_perform_create_logs_creation():
    serializer = ArticleSerializer(data={"title": "Titre", "status": "draft"})
    serializer.is_valid(raise_exception=True)

    ArticleViewSet().perform_create(serializer)

    entry = ActionLog.objects.get()
    assert entry.action == "CREATE"
    assert entry.object_repr == "Titre"


@pytest.mark.django_db
def test_perform_update_logs_diff():
    article = Article.objects.create(title="Titre", status="draft")
    serializer = ArticleSerializer(
        instance=article, data={"title": "Titre", "status": "published"}
    )
    serializer.is_valid(raise_exception=True)

    ArticleViewSet().perform_update(serializer)

    entry = ActionLog.objects.get()
    assert entry.action == "UPDATE"
    assert entry.changes["status"]["after"] == "published"


@pytest.mark.django_db
def test_perform_destroy_logs_delete():
    article = Article.objects.create(title="Titre", status="draft")

    ArticleViewSet().perform_destroy(article)

    entry = ActionLog.objects.get()
    assert entry.action == "DELETE"
    assert entry.object_id == str(article.pk)
