# Contribuer à django-forge-log

*[English](CONTRIBUTING.md) | Français*

Merci de vouloir contribuer ! Ce guide décrit comment mettre en place
l'environnement de développement et les attentes pour une pull request.

## Mise en place

Le projet utilise [uv](https://docs.astral.sh/uv/) pour la gestion des
dépendances et de l'environnement virtuel.

```bash
uv sync --group dev
```

## Vérifications avant de proposer une PR

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy
uv run pytest --cov=forge_log --cov-report=term-missing
```

La suite `pytest` tourne par défaut sur SQLite. Pour la faire tourner aussi
contre PostgreSQL et MySQL (recommandé pour toute modification du modèle
`ActionLog`, du diff ou des writers — un `JSONField`/`GenericIPAddressField`
peut se comporter différemment selon le dialecte) :

```bash
docker compose up -d
FORGE_LOG_TEST_DB=postgres uv run pytest
FORGE_LOG_TEST_DB=mysql uv run pytest
```

Ces mêmes vérifications tournent dans la CI (`.github/workflows/ci.yml`) et
doivent toutes passer avant qu'une PR soit mergeable :

- **ruff** : lint et formatage
- **mypy** (`strict = true`, avec `django-stubs`) : le typage doit rester
  précis, y compris sur le code qui touche à l'ORM et aux signaux Django
- **pytest** : sur les trois SGBD supportés (SQLite, PostgreSQL, MySQL) et
  contre Django 4.2/5.0/5.1/5.2 (SQLite). La suite couvre les cinq backends
  d'écriture (`sync`, `on_commit`, `thread`, `asyncio`, `celery`), le moteur
  de diff, le décorateur, le mixin DRF, l'Admin et l'intégration
  `django-signals-all`. La couverture est verrouillée à 100 %
  (`--cov-fail-under=100` via `[tool.coverage.report]`) : toute nouvelle
  branche de code doit être testée.

Si `pre-commit` est installé (`uv run pre-commit install`), ruff et mypy
tournent automatiquement avant chaque commit.

## Compatibilité

`django-forge-log` cible **Python 3.12+** et **Django 4.2+** (LTS courante
et versions suivantes). Toute PR doit rester compatible avec ces versions
minimales ; ne pas introduire de dépendance implicite à une version plus
récente sans en discuter d'abord dans une issue.

## Style de code

- Pas de commentaire qui explique le *quoi* (le code doit être lisible par
  lui-même) — seulement le *pourquoi* quand c'est non évident (contraintes
  cachées, comportement Django non documenté, contournement d'un bug connu).
- Pas d'abstraction ou de fonctionnalité ajoutée au-delà de ce que demande
  le changement.
- Le cœur (`forge_log.decorators`, `forge_log.middleware`, `forge_log.admin`,
  `forge_log.models`) ne doit jamais dépendre de DRF ni de
  `django-signals-all` — ces intégrations restent dans `forge_log.drf` et
  `forge_log.signals_integration`, chargées en extra (`[drf]`, `[signals]`).
  Un `import` direct de `rest_framework`/`django_signals_all` en dehors de
  ces deux modules est une régression.
- Tout nouveau champ journalisé par défaut (diff, contexte de requête) doit
  être passé au crible de la section Sécurité/PII du README avant d'être
  mergé : un champ sensible qui fuite dans `ActionLog.changes` est un bug
  de sévérité haute, pas un détail d'implémentation.

## Commits et PR

- Un message de commit clair, qui explique le *pourquoi* du changement.
- Une PR = un sujet. Préférer plusieurs petites PR à une seule PR fourre-tout.
- Décrire dans la description de la PR ce qui change et comment c'est testé.

## Politique de compatibilité et dépréciation

`django-forge-log` suit le [Semantic Versioning](https://semver.org/lang/fr/).
Le projet est actuellement en phase de *release candidate* (`1.0.0rcN`) :
l'API est considérée figée mais n'a pas encore été éprouvée par un usage
réel en dehors de ce dépôt — voir la
[politique release candidate](RELEASING.fr.md#politique-release-candidate-avant-le-100-final)
dans RELEASING.md pour ce qui peut/ne peut pas changer d'une RC à l'autre.

À partir de `1.0.0` :

- un **major** (`X.0.0`) peut casser la compatibilité ;
- un **minor** (`1.X.0`) ajoute des fonctionnalités sans rien casser ;
- un **patch** (`1.0.X`) ne contient que des corrections de bug.

Après `1.0.0`, toute API publique dépréciée continue de fonctionner et lève
un `DeprecationWarning` explicite pendant au moins une version mineure
complète avant d'être retirée dans un major suivant.

## Signaler un bug ou proposer une fonctionnalité

Ouvrez une [issue](https://github.com/alzeph/django-forge-log/issues) en
utilisant le template approprié. Pour une faille de sécurité, voir
[SECURITY.md](SECURITY.fr.md) plutôt qu'une issue publique.
