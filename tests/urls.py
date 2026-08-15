from django.urls import include, path
from rest_framework.routers import DefaultRouter

from tests import views

router = DefaultRouter()
router.register("articles", views.ArticleViewSet, basename="article")

urlpatterns = [
    path("articles/<int:pk>/update/", views.update_article, name="update-article"),
    path("api/", include(router.urls)),
]
