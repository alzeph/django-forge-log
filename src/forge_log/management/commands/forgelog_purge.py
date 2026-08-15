from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from forge_log.conf import app_settings
from forge_log.models import ActionLog


class Command(BaseCommand):
    help = "Purge les entrées ActionLog plus vieilles que FORGE_LOG['RETENTION_DAYS']."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help="Rétention en jours (défaut : FORGE_LOG['RETENTION_DAYS']).",
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:
        days = (
            options["days"]
            if options["days"] is not None
            else app_settings.RETENTION_DAYS
        )
        if not days:
            self.stderr.write(
                "Aucune rétention configurée (FORGE_LOG['RETENTION_DAYS'] ou --days)."
            )
            return

        cutoff = timezone.now() - timedelta(days=days)
        queryset = ActionLog.objects.filter(timestamp__lt=cutoff)
        count = queryset.count()

        if options["dry_run"]:
            self.stdout.write(f"{count} entrée(s) seraient supprimées (dry-run).")
            return

        queryset.delete()
        self.stdout.write(self.style.SUCCESS(f"{count} entrée(s) supprimée(s)."))
