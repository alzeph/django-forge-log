# django-forge-log

[![CI](https://github.com/alzeph/django-forge-log/actions/workflows/ci.yml/badge.svg)](https://github.com/alzeph/django-forge-log/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/django-forge-log.svg)](https://pypi.org/project/django-forge-log/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)

> **Release candidate.** `django-forge-log` est en `1.0.0rc1` : l'API est
> considérée figée mais n'a pas encore été éprouvée par un usage réel en
> dehors de ce dépôt. Les retours (issues, cas d'usage, bugs) sont les
> bienvenus avant de tagger la version `1.0.0` finale — voir
> [RELEASING.md](RELEASING.md).

Un audit trail léger et automatique — Qui, Quoi, Quand, Où, et le Diff
avant/après — pour les vues Django (FBV, CBV, DRF ViewSets) et l'Admin,
stocké dans une seule table JSON centrale.

## Le problème

Le `LogEntry` natif de `django.contrib.admin` ne trace que ce qui passe par
l'Admin. Dès qu'une mutation passe par une API DRF, une vue classique ou un
script, plus rien n'est journalisé. `django-simple-history`/`django-reversion`
résolvent ça en dupliquant une table par modèle suivi — lourd, et ça
n'explique pas *qui* a fait le changement ni *depuis où*. `django-forge-log`
vise une piste d'audit unique et compacte, avec un typage strict du diff.

## Installation

Le cœur (middleware, décorateur, moteur de diff, Admin) ne dépend que de
Django et Pydantic. Les intégrations DRF, `django-signals-all` et Celery
sont des extras à activer séparément, à combiner selon les besoins :

```bash
# Cœur seul
uv add django-forge-log

# Avec l'intégration DRF (forge_log.drf.AuditViewSetMixin)
uv add "django-forge-log[drf]"

# Avec l'intégration bulk django-signals-all (bulk_create/bulk_update/.update())
uv add "django-forge-log[signals]"

# Avec le backend d'écriture Celery (WRITE_BACKEND="celery")
uv add "django-forge-log[celery]"

# Plusieurs extras à la fois
uv add "django-forge-log[drf,signals,celery]"
```

Avec `pip`, mêmes combinaisons :

```bash
pip install django-forge-log
pip install "django-forge-log[drf,signals,celery]"
```

`rc1` n'étant pas encore une version finale, PyPI ne l'installe pas par
défaut avec `pip install django-forge-log` — utilisez `--pre` ou fixez la
version exacte tant que `1.0.0` n'est pas taggé :

```bash
uv add "django-forge-log==1.0.0rc1"
pip install "django-forge-log==1.0.0rc1"
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

## Démarrage rapide

### Vue générique (FBV/CBV)

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

Sans configuration, l'instance suivie est retrouvée via le PK présent dans
les kwargs de la vue (`pk`, ou le nom du champ clé primaire du modèle) — le
cas courant `/resource/<pk>/`. Pour une création (pas de PK dans l'URL avant
l'exécution de la vue), fournissez `get_instance` explicitement, ou préférez
le mixin DRF ci-dessous.

### ViewSet DRF

```python
from rest_framework.viewsets import ModelViewSet
from forge_log.drf import AuditViewSetMixin


class ArticleViewSet(AuditViewSetMixin, ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
```

Capture nativement `create`/`update`/`partial_update`/`destroy`, y compris
les créations (contrairement à `track_action`, qui a besoin d'un PK dans
l'URL). Nécessite l'extra `django-forge-log[drf]`.

### Admin

```python
from django.contrib import admin
from forge_log.admin import AuditModelAdminMixin


@admin.register(Article)
class ArticleAdmin(AuditModelAdminMixin, admin.ModelAdmin):
    pass
```

La table `ActionLog` elle-même est consultable (lecture seule) dans
l'Admin via `forge_log.admin.ActionLogAdmin`.

### Opérations en masse (`bulk_create`, `bulk_update`, `.update()`)

Ces opérations contournent `Model.save()` et aucune des trois intégrations
ci-dessus ne peut les voir depuis la vue. En branchant
[django-signals-all](https://pypi.org/project/django-signals-all/) (extra
`django-forge-log[signals]`), les mutations bulk émises via son
`BulkSignalManager` sont journalisées automatiquement, sans code
supplémentaire :

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

`.filter(...).update(...)` ne charge pas les instances modifiées : une seule
entrée agrégée est journalisée (`action="BULK_UPDATE"`, `object_id=None`),
avec la liste des PK impactés dans `metadata`. `bulk_create()` et
`Manager.bulk_update()` journalisent en revanche une entrée par instance.

## Écriture asynchrone (`WRITE_BACKEND`)

Écrire dans `ActionLog` a un coût. Cinq backends, sélectionnables par
projet ou pour un test :

| Backend | Comportement | Durabilité | Coût sur la requête |
|---|---|---|---|
| `sync` | Écrit immédiatement | Maximale, mais journalise même une transaction annulée | Élevé |
| `on_commit` | `transaction.on_commit()` | Jamais loggé si rollback | Élevé (toujours avant la réponse) |
| `thread` (**défaut**) | File en mémoire + thread démon, `bulk_create` par lots | Fenêtre de perte (~200 ms) si le process est tué | Quasi nul (`queue.put_nowait`) |
| `asyncio` | `asyncio.create_task()` (vues `async def`) | Idem `thread` ; nécessite un event loop actif | Quasi nul |
| `celery` | Dispatch total via une tâche Celery | Robuste (persiste dans le broker) | Quasi nul |

```python
FORGE_LOG = {
    "WRITE_BACKEND": "thread",  # "sync" | "on_commit" | "thread" | "asyncio" | "celery"
}
```

`celery` nécessite l'extra `django-forge-log[celery]` et un broker déjà
configuré côté projet.

## Sécurité et PII

Le diff peut exposer des données sensibles s'il n'est pas configuré :

```python
FORGE_LOG = {
    # Champs jamais journalisés (avant *et* après), par motif regex.
    "EXCLUDED_FIELDS": [r".*secret.*", r".*token.*", r".*_key$", r"credit_card", r"ssn"],
    # Champs journalisés comme "modifiés" sans exposer les valeurs :
    # {"password": {"masked": true}} plutôt que {"before": ..., "after": ...}.
    "MASKED_FIELDS": ["password"],
}
```

Ces réglages peuvent aussi être fixés par modèle, ce qui prime sur la config
globale :

```python
class Article(models.Model):
    ...
    class ForgeLogMeta:
        excluded_fields = ["internal_note"]
        masked_fields = []
```

Les `FileField`/`ImageField` ne journalisent jamais de contenu binaire,
seulement le chemin (`.name`).

## Rétention

```bash
python manage.py forgelog_purge --days 90         # supprime les entrées de plus de 90 jours
python manage.py forgelog_purge --days 90 --dry-run
```

Ou via `FORGE_LOG["RETENTION_DAYS"]` pour ne pas avoir à passer `--days` à
chaque appel (à brancher sur un cron applicatif — `forgelog_purge` ne
s'exécute jamais tout seul).

## Configuration complète

```python
FORGE_LOG = {
    "ENABLED": True,
    "WRITE_BACKEND": "thread",
    "EXCLUDED_FIELDS": [r".*secret.*", r".*token.*", r".*_key$", r"credit_card", r"ssn"],
    "MASKED_FIELDS": ["password"],
    "RETENTION_DAYS": None,
    "THREAD_FLUSH_INTERVAL": 0.2,     # secondes, backend "thread"
    "THREAD_MAX_BATCH_SIZE": 50,      # backend "thread"
    "THREAD_MAX_QUEUE_SIZE": 10_000,  # backend "thread"
}
```

## Limitations connues

- `object_id` est un `CharField` (pas une FK typée) pour supporter les PK
  non entières (UUID) sans une table par modèle — même compromis que
  `django-reversion`/`django-guardian`. Un index composite
  `(content_type, object_id)` compense l'absence de contrainte FK native.
- `track_action` sans `get_instance` ne peut pas capturer une création (pas
  de PK dans l'URL avant l'exécution de la vue) : utilisez
  `forge_log.drf.AuditViewSetMixin` pour un ViewSet DRF, ou fournissez
  `get_instance` explicitement.
- Backend `thread` : les entrées en file d'attente sont perdues si le
  process est tué avant le prochain flush (~`THREAD_FLUSH_INTERVAL`). Pour
  une garantie stricte de durabilité, utilisez `on_commit` ou `celery`.
- Le diff ne compare que les champs concrets du modèle (`_meta.concrete_fields`)
  ou la liste explicite passée à `fields=` — pas les relations M2M implicites.

## Développement

```bash
uv sync --group dev

uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy

# SQLite (par défaut, pas de dépendance externe)
uv run pytest --cov=forge_log --cov-report=term-missing

# PostgreSQL et MySQL (nécessite Docker)
docker compose up -d
FORGE_LOG_TEST_DB=postgres uv run pytest
FORGE_LOG_TEST_DB=mysql uv run pytest
```

Voir [CONTRIBUTING.md](CONTRIBUTING.md) pour contribuer,
[CHANGELOG.md](CHANGELOG.md) pour l'historique des versions, et
[RELEASING.md](RELEASING.md) pour le processus de publication.

## Licence

[MIT](LICENSE)
