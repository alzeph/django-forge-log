# Changelog

*English | [Français](CHANGELOG.fr.md)*

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0rc3] - 2026-08-15

### Added

- Support for `async def` views in `track_action` (detected via
  `asgiref.sync.iscoroutinefunction`, `get_instance`/diff/write switched
  to `sync_to_async`).
- `ActionLog.objects.for_object(instance)`: an object's history, most
  recent first, chainable with `.filter(...)`.
- `forge_log.relations.ForgeLogRelationMixin`: optional
  `instance.forge_log_entries` on a tracked model — an abstract class
  with a Python property, **not** a `GenericRelation` (see Fixed
  below).
- End-to-end integration tests (real `Client`/`APIClient`, middleware +
  decorator/mixin + writer) in addition to the existing unit tests.

### Fixed

- **`ActionLog.objects.for_object`/`forge_log_entries` implemented via
  `GenericRelation` would have deleted an object's audit history on
  deletion**: `GenericRelation` forces `on_delete=CASCADE` in a way
  that cannot be configured on the Django side. Caught by an
  end-to-end integration test (update then delete on the same object)
  before being published — implemented as a plain Python property
  instead, never as a `GenericRelation`.
- **`AuditViewSetMixin.perform_destroy`/`AuditModelAdminMixin.delete_model`
  logged an empty `object_id`**: `Model.delete()` sets `instance.pk` to
  `None` in place, and the object was re-read after the deletion to
  build the entry. A snapshot (`copy.copy`) is now captured before the
  call to `delete()`. The existing unit test did not catch the bug: it
  re-read the same already-mutated variable for its assertion.
- **A user authenticated by DRF (`TokenAuthentication`, JWT...) could
  be logged as `"anonymous"`**: DRF authentication runs during view
  dispatch, after `RequestContextMiddleware` has already run, which
  froze `request.user` too early. The context
  (`forge_log.context.get_current_context`) is now resolved at read
  time rather than write time, from a live reference to `request`
  rather than a snapshot.

## [1.0.0rc2] - 2026-08-15

Hardening only (no public API change): five bugs identified during a
review of the rc1 version, before they could affect real-world usage.

### Fixed

- **Crash on tracked `DecimalField`/`UUIDField`**: `JSONField` uses the
  standard JSON encoder by default, which raises `TypeError` on
  `Decimal` and `UUID`. A model with a simple price field crashed the
  write as soon as it changed. `changes`/`metadata` now use
  `DjangoJSONEncoder` (also natively handles `datetime`/`date`/`UUID`/
  `Decimal`) — migration included.
- **N+1 queries on tracked `ForeignKey` fields**: the diff read the
  related object (`instance.parent`) instead of just the `parent_id`
  column, triggering one query per instance not already cached. This
  contradicted the near-zero-cost promise of the `thread`/`asyncio`
  backends.
- **Race condition on the `get_writer()` singleton**: without a lock,
  two threads of a threaded WSGI server (gunicorn `--threads`, gthread)
  could each start their own `ThreadedWriter`, leaving an orphaned
  daemon thread never stopped by `reset_writer()`.
- **Missing truncation on `ActionLog`'s `CharField`s**:
  `object_repr`/`user_repr`/`action` not truncated before the write
  could crash the insert on PostgreSQL (`varchar(n)` strict, unlike
  SQLite which silently tolerates overflow).
- **Unvalidated `X-Forwarded-For`** before storage in
  `GenericIPAddressField`: a header entirely controllable by the
  client, a malformed value crashed the write on PostgreSQL (strict
  `inet` type). Now validated via `ipaddress.ip_address()`, `None` if
  invalid.

## [1.0.0rc1] - 2026-08-15

### Added

- `ActionLog` model: single central audit table (Who/What/When/Where/
  Diff), indexed on `(content_type, object_id)`.
- `forge_log.middleware.RequestContextMiddleware`: captures Who/Where
  via `contextvars` (ASGI-compatible).
- `forge_log.diff.compute_diff` + `forge_log.schemas` (Pydantic v2):
  strict diff engine, with `EXCLUDED_FIELDS`/`MASKED_FIELDS` (global
  config or per-model `ForgeLogMeta`).
- `forge_log.decorators.track_action`: generic decorator for FBV/CBV.
- `forge_log.drf.AuditViewSetMixin`: DRF integration (`[drf]` extra)
  that also captures creations, unlike the generic decorator.
- `forge_log.admin.AuditModelAdminMixin` and `ActionLogAdmin`: Admin
  integration and read-only browsing of the audit trail.
- `forge_log.signals_integration`: `django-signals-all` integration
  (`[signals]` extra) to log `bulk_create`/`bulk_update`/`.update()`.
- Five pluggable write backends (`FORGE_LOG["WRITE_BACKEND"]`): `sync`,
  `on_commit`, `thread` (default), `asyncio`, `celery` (`[celery]`
  extra) — to decouple the write from the tracked request path.
- `forgelog_purge` command for retention.
- `forge_log.signals.action_logged` signal for extensibility.
- Multi-database CI (SQLite, PostgreSQL, MySQL via
  `docker-compose.yml`) and test coverage locked at 100%
  (`--cov-fail-under=100`).

### Fixed

- `compute_diff` compared raw values before serialization: two
  `FieldFile` instances from two different instances are never equal
  via `==` (no `__eq__` defined), so an unchanged `FileField` could
  wrongly appear as modified in the diff. The comparison now happens
  on the already-serialized values.

[Unreleased]: https://github.com/alzeph/django-forge-log/compare/v1.0.0rc3...main
[1.0.0rc3]: https://github.com/alzeph/django-forge-log/compare/v1.0.0rc2...v1.0.0rc3
[1.0.0rc2]: https://github.com/alzeph/django-forge-log/compare/v1.0.0rc1...v1.0.0rc2
[1.0.0rc1]: https://github.com/alzeph/django-forge-log/commits/v1.0.0rc1
