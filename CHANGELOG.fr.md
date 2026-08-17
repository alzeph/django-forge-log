# Changelog

*[English](CHANGELOG.md) | Français*

Toutes les modifications notables de ce projet sont documentées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [Unreleased]

## [1.0.0rc3] - 2026-08-15

### Added

- Support des vues `async def` pour `track_action` (détection via
  `asgiref.sync.iscoroutinefunction`, `get_instance`/diff/écriture basculés
  sur `sync_to_async`).
- `ActionLog.objects.for_object(instance)` : historique d'un objet, du plus
  récent au plus ancien, chaînable avec `.filter(...)`.
- `forge_log.relations.ForgeLogRelationMixin` : `instance.forge_log_entries`
  optionnel sur un modèle suivi — une classe abstraite avec une propriété
  Python, **pas** un `GenericRelation` (voir Fixed ci-dessous).
- Tests d'intégration bout-en-bout (`Client`/`APIClient` réels, middleware +
  décorateur/mixin + writer) en plus des tests unitaires existants.

### Fixed

- **`ActionLog.objects.for_object`/`forge_log_entries` implémentés via
  `GenericRelation` auraient supprimé l'historique d'audit d'un objet à sa
  suppression** : `GenericRelation` impose `on_delete=CASCADE` de façon non
  configurable côté Django. Détecté par un test d'intégration bout-en-bout
  (update puis delete sur le même objet) avant d'être publié — implémenté
  comme une simple propriété Python à la place, jamais comme un
  `GenericRelation`.
- **`AuditViewSetMixin.perform_destroy`/`AuditModelAdminMixin.delete_model`
  journalisaient un `object_id` vide** : `Model.delete()` met `instance.pk`
  à `None` en place, et l'objet était relu après la suppression pour
  construire l'entrée. Un instantané (`copy.copy`) est maintenant capturé
  avant l'appel à `delete()`. Le test unitaire existant ne détectait pas le
  bug : il relisait la même variable déjà mutée pour son assertion.
- **Un utilisateur authentifié par DRF (`TokenAuthentication`, JWT...)
  pouvait être journalisé comme `"anonymous"`** : l'authentification DRF
  s'exécute pendant le dispatch de la vue, après le passage de
  `RequestContextMiddleware`, qui figeait `request.user` trop tôt. Le
  contexte (`forge_log.context.get_current_context`) est maintenant résolu
  à la lecture plutôt qu'à l'écriture, à partir d'une référence vivante à
  `request` plutôt que d'un instantané.

## [1.0.0rc2] - 2026-08-15

Durcissement uniquement (aucun changement d'API publique) : cinq bugs
identifiés lors d'une revue de la version rc1, avant qu'ils ne touchent un
usage réel.

### Fixed

- **Crash sur `DecimalField`/`UUIDField` suivi** : `JSONField` utilise
  l'encodeur JSON standard par défaut, qui lève `TypeError` sur `Decimal`
  et `UUID`. Un modèle avec un simple champ de prix faisait planter
  l'écriture dès qu'il changeait. `changes`/`metadata` utilisent maintenant
  `DjangoJSONEncoder` (gère aussi `datetime`/`date`/`UUID`/`Decimal`
  nativement) — migration incluse.
- **Requêtes N+1 sur les champs `ForeignKey` suivis** : le diff lisait
  l'objet lié (`instance.parent`) au lieu de la seule colonne `parent_id`,
  déclenchant une requête par instance non déjà mise en cache. Contredisait
  la promesse de coût quasi nul des backends `thread`/`asyncio`.
- **Condition de course sur le singleton `get_writer()`** : sans verrou,
  deux threads d'un serveur WSGI threadé (gunicorn `--threads`, gthread)
  pouvaient démarrer chacun leur propre `ThreadedWriter`, laissant un
  thread démon orphelin jamais arrêté par `reset_writer()`.
- **Troncature manquante sur les `CharField` de `ActionLog`** :
  `object_repr`/`user_repr`/`action` non tronqués avant écriture pouvaient
  faire planter l'insertion sur PostgreSQL (`varchar(n)` strict, contrairement
  à SQLite qui tolère silencieusement).
- **`X-Forwarded-For` non validé** avant stockage dans
  `GenericIPAddressField` : header entièrement contrôlable par le client,
  une valeur malformée faisait planter l'écriture sur PostgreSQL (type
  `inet` strict). Validé via `ipaddress.ip_address()` désormais, `None` si
  invalide.

## [1.0.0rc1] - 2026-08-15

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

[Unreleased]: https://github.com/alzeph/django-forge-log/compare/v1.0.0rc3...main
[1.0.0rc3]: https://github.com/alzeph/django-forge-log/compare/v1.0.0rc2...v1.0.0rc3
[1.0.0rc2]: https://github.com/alzeph/django-forge-log/compare/v1.0.0rc1...v1.0.0rc2
[1.0.0rc1]: https://github.com/alzeph/django-forge-log/commits/v1.0.0rc1
