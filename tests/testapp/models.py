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

    class ForgeLogMeta:
        excluded_fields = ["internal_note"]

    def __str__(self) -> str:
        return self.title
