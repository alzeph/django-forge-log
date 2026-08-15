from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, default="draft")
    internal_note = models.CharField(max_length=200, blank=True, default="")
    published_at = models.DateTimeField(null=True, blank=True)
    cover = models.FileField(upload_to="covers/", blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    # Pas de default=uuid.uuid4 : deux Article(...) construits sans argument
    # explicite doivent rester comparables (même valeur None) dans les tests
    # de diff, plutôt que de générer chacun un UUID aléatoire différent.
    external_ref = models.UUIDField(null=True, blank=True)

    class ForgeLogMeta:
        excluded_fields = ["internal_note"]

    def __str__(self) -> str:
        return self.title
