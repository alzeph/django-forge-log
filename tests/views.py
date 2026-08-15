from __future__ import annotations

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from forge_log.decorators import track_action
from forge_log.drf import AuditViewSetMixin
from tests.testapp.models import Article


# HTML classique : formulaire POST-only pour une mise à jour (pas de PUT/PATCH
# côté navigateur). _HTTP_METHOD_TO_ACTION mapperait POST -> CREATE par
# défaut, donc l'action est fixée explicitement ici.
@track_action(Article, action="UPDATE")
def update_article(request, pk):
    article = Article.objects.get(pk=pk)
    article.status = request.POST.get("status", article.status)
    article.save()
    return JsonResponse({"id": article.pk, "status": article.status})


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "status"]


class StaticTokenAuthentication(TokenAuthentication):
    """Authentification DRF minimale pour les tests : le "token" est le
    username, sans dépendance à rest_framework.authtoken (non installé)."""

    def authenticate(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth.startswith("Bearer "):
            return None
        username = auth.removeprefix("Bearer ")
        return (get_user_model().objects.get(username=username), None)


class ArticleViewSet(AuditViewSetMixin, ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    # authentication_classes doit être fixé à la définition de la classe : la
    # valeur par défaut de DRF (api_settings.DEFAULT_AUTHENTICATION_CLASSES)
    # est résolue une fois à l'import de rest_framework.views, pas relue à
    # chaque requête — modifier settings.REST_FRAMEWORK au runtime (ex. dans
    # un test) n'a aucun effet sur une vue déjà importée.
    authentication_classes = [SessionAuthentication, StaticTokenAuthentication]
