# django-forge-log

[![CI](https://github.com/alzeph/django-forge-log/actions/workflows/ci.yml/badge.svg)](https://github.com/alzeph/django-forge-log/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/django-forge-log.svg)](https://pypi.org/project/django-forge-log/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)

*English | [Français](README.fr.md)*

> **Release candidate.** `django-forge-log` is at `1.0.0rc3`: the API is
> considered frozen but has not yet been exercised by real-world usage
> outside of this repository. Feedback (issues, use cases, bugs) is
> welcome before the final `1.0.0` is tagged — see
> [RELEASING.md](RELEASING.md).

A lightweight, automatic audit trail — Who, What, When, Where, and the
before/after Diff — for Django views (FBV, CBV, DRF ViewSets) and the
Admin, stored in a single central JSON table.

## The problem

The native `LogEntry` from `django.contrib.admin` only tracks what goes
through the Admin. As soon as a mutation goes through a DRF API, a plain
view, or a script, nothing gets logged anymore. `django-simple-history`/
`django-reversion` solve this by duplicating a table per tracked model —
heavy, and it doesn't explain *who* made the change or *from where*.
`django-forge-log` aims for a single, compact audit trail, with strict
typing on the diff.

## Installation

The core (middleware, decorator, diff engine, Admin) only depends on
Django and Pydantic. The DRF, `django-signals-all`, and Celery
integrations are separate extras to enable, combined as needed:

```bash
# Core only
uv add django-forge-log

# With the DRF integration (forge_log.drf.AuditViewSetMixin)
uv add "django-forge-log[drf]"

# With the django-signals-all bulk integration (bulk_create/bulk_update/.update())
uv add "django-forge-log[signals]"

# With the Celery write backend (WRITE_BACKEND="celery")
uv add "django-forge-log[celery]"

# Several extras at once
uv add "django-forge-log[drf,signals,celery]"
```

With `pip`, same combinations:

```bash
pip install django-forge-log
pip install "django-forge-log[drf,signals,celery]"
```

Since a release candidate is not a final version, PyPI does not install
it by default with `pip install django-forge-log` — use `--pre` or pin
the exact version until `1.0.0` is tagged:

```bash
uv add "django-forge-log==1.0.0rc3"
pip install "django-forge-log==1.0.0rc3"
```

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "django.contrib.contenttypes",
    "forge_log",
]

MIDDLEWARE = [
    ...,
    "forge_log.middleware.RequestContextMiddleware",
]
```

```bash
python manage.py migrate forge_log
```

## Quick start

### Generic view (FBV/CBV)

```python
from forge_log.decorators import track_action
from .models import Article


@track_action(Article)
def update_article(request, pk):
    article = Article.objects.get(pk=pk)
    article.status = "published"
    article.save()
    return HttpResponse(...)
```

Without configuration, the tracked instance is looked up via the PK
present in the view kwargs (`pk`, or the model's primary key field name)
— the common `/resource/<pk>/` case. For a creation (no PK in the URL
before the view runs), provide `get_instance` explicitly, or prefer the
DRF mixin below.

`async def` views are detected automatically (`get_instance`, the diff
computation, and the write then switch to `sync_to_async`):

```python
@track_action(Article)
async def update_article(request, pk):
    article = await Article.objects.aget(pk=pk)
    article.status = "published"
    await article.asave()
    return JsonResponse(...)
```

With `WRITE_BACKEND="asyncio"`, this path runs on the executor thread
rather than on the event loop: the write then falls back to
`AsyncTaskWriter`'s synchronous mode rather than `asyncio.create_task()`
— still correct, but without the expected performance gain. Prefer
`thread` or `celery` for high-traffic tracked async views.

### DRF ViewSet

```python
from rest_framework.viewsets import ModelViewSet
from forge_log.drf import AuditViewSetMixin


class ArticleViewSet(AuditViewSetMixin, ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

Natively captures `create`/`update`/`partial_update`/`destroy`,
including creations (unlike `track_action`, which needs a PK in the
URL). Requires the `django-forge-log[drf]` extra.

### Admin

```python
from django.contrib import admin
from forge_log.admin import AuditModelAdminMixin


@admin.register(Article)
class ArticleAdmin(AuditModelAdminMixin, admin.ModelAdmin):
    pass
```

The `ActionLog` table itself is browsable (read-only) in the Admin via
`forge_log.admin.ActionLogAdmin`.

### Bulk operations (`bulk_create`, `bulk_update`, `.update()`)

These operations bypass `Model.save()` and none of the three
integrations above can see them from the view. By wiring up
[django-signals-all](https://pypi.org/project/django-signals-all/)
(`django-forge-log[signals]` extra), bulk mutations emitted through its
`BulkSignalManager` are logged automatically, with no extra code:

```python
# models.py
from django.db import models
from django_signals_all.orm.manager import BulkSignalManager


class Article(models.Model):
    ...
    objects = BulkSignalManager()
```

```python
# settings.py
INSTALLED_APPS = [..., "django_signals_all", "forge_log"]
```

`.filter(...).update(...)` does not load the modified instances: a
single aggregated entry is logged (`action="BULK_UPDATE"`,
`object_id=None`), with the list of impacted PKs in `metadata`.
`bulk_create()` and `Manager.bulk_update()`, on the other hand, log one
entry per instance.

## Object history

```python
ActionLog.objects.for_object(article)          # QuerySet, most recent first
ActionLog.objects.for_object(article).filter(action="UPDATE")
```

Or directly from the instance, by adding the mixin to the tracked
model:

```python
from forge_log.relations import ForgeLogRelationMixin


class Article(ForgeLogRelationMixin, models.Model):
    ...


article.forge_log_entries.all()  # equivalent to ActionLog.objects.for_object(article)
```

`ForgeLogRelationMixin` is an abstract class (no concrete field, so no
migration required), deliberately **not** a `GenericRelation`:
`GenericRelation` forces `on_delete=CASCADE` in a way that cannot be
configured on the Django side, which would delete an object's entire
audit history at the exact moment it is deleted — the opposite of what
an audit trail must guarantee.

## Asynchronous writes (`WRITE_BACKEND`)

Writing to `ActionLog` has a cost. Five backends, selectable per
project or per test:

| Backend | Behavior | Durability | Cost on the request |
|---|---|---|---|
| `sync` | Writes immediately | Maximal, but logs even a rolled-back transaction | High |
| `on_commit` | `transaction.on_commit()` | Never logged on rollback | High (always before the response) |
| `thread` (**default**) | In-memory queue + daemon thread, `bulk_create` in batches | Loss window (~200 ms) if the process is killed | Near zero (`queue.put_nowait`) |
| `asyncio` | `asyncio.create_task()` (`async def` views) | Same as `thread`; requires an active event loop | Near zero |
| `celery` | Full dispatch via a Celery task | Robust (persisted in the broker) | Near zero |

```python
FORGE_LOG = {
    "WRITE_BACKEND": "thread",  # "sync" | "on_commit" | "thread" | "asyncio" | "celery"
}
```

`celery` requires the `django-forge-log[celery]` extra and a broker
already configured on the project side.

## Security and PII

The diff can expose sensitive data if left unconfigured:

```python
FORGE_LOG = {
    # Fields never logged (before *and* after), by regex pattern.
    "EXCLUDED_FIELDS": [r".*secret.*", r".*token.*", r".*_key$", r"credit_card", r"ssn"],
    # Fields logged as "changed" without exposing the values:
    # {"password": {"masked": true}} rather than {"before": ..., "after": ...}.
    "MASKED_FIELDS": ["password"],
}
```

These settings can also be set per model, which takes precedence over
the global config:

```python
class Article(models.Model):
    ...
    class ForgeLogMeta:
        excluded_fields = ["internal_note"]
        masked_fields = []
```

`FileField`/`ImageField` never log binary content, only the path
(`.name`).

## Retention

```bash
python manage.py forgelog_purge --days 90         # deletes entries older than 90 days
python manage.py forgelog_purge --days 90 --dry-run
```

Or via `FORGE_LOG["RETENTION_DAYS"]` to avoid passing `--days` on every
call (to wire up to an application cron — `forgelog_purge` never runs
on its own).

## Full configuration

```python
FORGE_LOG = {
    "ENABLED": True,
    "WRITE_BACKEND": "thread",
    "EXCLUDED_FIELDS": [r".*secret.*", r".*token.*", r".*_key$", r"credit_card", r"ssn"],
    "MASKED_FIELDS": ["password"],
    "RETENTION_DAYS": None,
    "THREAD_FLUSH_INTERVAL": 0.2,     # seconds, "thread" backend
    "THREAD_MAX_BATCH_SIZE": 50,      # "thread" backend
    "THREAD_MAX_QUEUE_SIZE": 10_000,  # "thread" backend
}
```

## Known limitations

- `object_id` is a `CharField` (not a typed FK) to support non-integer
  PKs (UUID) without a table per model — the same trade-off as
  `django-reversion`/`django-guardian`. A composite index
  `(content_type, object_id)` compensates for the lack of a native FK
  constraint.
- `track_action` without `get_instance` cannot capture a creation (no
  PK in the URL before the view runs): use
  `forge_log.drf.AuditViewSetMixin` for a DRF ViewSet, or provide
  `get_instance` explicitly.
- `thread` backend: queued entries are lost if the process is killed
  before the next flush (~`THREAD_FLUSH_INTERVAL`). For a strict
  durability guarantee, use `on_commit` or `celery`.
- The diff only compares the model's concrete fields
  (`_meta.concrete_fields`) or the explicit list passed to `fields=` —
  not implicit M2M relations.

## Development

```bash
uv sync --group dev

uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy

# SQLite (default, no external dependency)
uv run pytest --cov=forge_log --cov-report=term-missing

# PostgreSQL and MySQL (requires Docker)
docker compose up -d
FORGE_LOG_TEST_DB=postgres uv run pytest
FORGE_LOG_TEST_DB=mysql uv run pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute,
[CHANGELOG.md](CHANGELOG.md) for the release history, and
[RELEASING.md](RELEASING.md) for the publishing process.

## License

[MIT](LICENSE)
