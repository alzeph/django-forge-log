from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from forge_log.models import ActionLogQuerySet


class ForgeLogRelationMixin(models.Model):
    """Mixin optionnel : ajoute `instance.forge_log_entries` sur un modèle suivi.

        class Article(ForgeLogRelationMixin, models.Model):
            ...

        article.forge_log_entries.all()  # équivalent à
        ActionLog.objects.for_object(article)

    Volontairement une simple propriété Python, pas un `GenericRelation` :
    `GenericRelation` force `on_delete=CASCADE` côté Django (non
    configurable — voir `GenericRelation.__init__`, qui l'impose
    inconditionnellement) : supprimer l'objet suivi supprimerait alors tout
    son historique d'audit avec lui, l'inverse de ce qu'un audit trail doit
    garantir. Une classe de base abstraite (`abstract = True`) plutôt qu'un
    mixin Python nu : ne déclare aucun champ concret, donc aucune migration
    requise côté application, tout en typant correctement `self`.
    """

    class Meta:
        abstract = True

    @property
    def forge_log_entries(self) -> ActionLogQuerySet:
        from forge_log.models import ActionLog

        return ActionLog.objects.for_object(self)
