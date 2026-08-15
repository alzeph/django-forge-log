# Changelog

Toutes les modifications notables de ce projet sont documentées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [Unreleased]

### Added

- Modèle `ActionLog` : table d'audit centrale unique (Qui/Quoi/Quand/Où/Diff),
  indexée sur `(content_type, object_id)`.
- `forge_log.middleware.RequestContextMiddleware` : capture Qui/Où via
  `contextvars` (compatible ASGI).
- `forge_log.diff.compute_diff` + `forge_log.schemas` (Pydantic v2) : moteur
  de diff strict, avec `EXCLUDED_FIELDS`/`MASKED_FIELDS` (config globale ou
  `ForgeLogMeta` par modèle).
- `forge_log.decorators.track_action` : décorateur générique pour FBV/CBV.
- `forge_log.drf.AuditViewSetMixin` : intégration DRF (extra `[drf]`) qui
  capture aussi les créations, contrairement au décorateur générique.
- `forge_log.admin.AuditModelAdminMixin` et `ActionLogAdmin` : intégration
  Admin et consultation en lecture seule de la piste d'audit.
- `forge_log.signals_integration` : intégration `django-signals-all` (extra
  `[signals]`) pour journaliser `bulk_create`/`bulk_update`/`.update()`.
- Cinq backends d'écriture pluggables (`FORGE_LOG["WRITE_BACKEND"]`) :
  `sync`, `on_commit`, `thread` (défaut), `asyncio`, `celery` (extra
  `[celery]`) — pour découpler l'écriture du chemin de requête suivi.
- Commande `forgelog_purge` pour la rétention.
- Signal `forge_log.signals.action_logged` pour l'extensibilité.
- CI multi-SGBD (SQLite, PostgreSQL, MySQL via `docker-compose.yml`) et
  couverture de tests verrouillée à 100 % (`--cov-fail-under=100`).

### Fixed

- `compute_diff` comparait les valeurs brutes avant sérialisation : deux
  `FieldFile` de deux instances différentes n'étant jamais égaux via `==`
  (pas d'`__eq__` défini), un `FileField` inchangé pouvait apparaître à tort
  comme modifié dans le diff. La comparaison se fait maintenant sur les
  valeurs déjà sérialisées.

[Unreleased]: https://github.com/alzeph/django-forge-log/commits/main
