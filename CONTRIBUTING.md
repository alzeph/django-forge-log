# Contributing to django-forge-log

*English | [Français](CONTRIBUTING.fr.md)*

Thanks for wanting to contribute! This guide describes how to set up
the development environment and what's expected from a pull request.

## Setup

The project uses [uv](https://docs.astral.sh/uv/) for dependency and
virtual environment management.

```bash
uv sync --group dev
```

## Checks before submitting a PR

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy
uv run pytest --cov=forge_log --cov-report=term-missing
```

The `pytest` suite runs against SQLite by default. To also run it
against PostgreSQL and MySQL (recommended for any change touching the
`ActionLog` model, the diff, or the writers — a
`JSONField`/`GenericIPAddressField` can behave differently depending
on the dialect):

```bash
docker compose up -d
FORGE_LOG_TEST_DB=postgres uv run pytest
FORGE_LOG_TEST_DB=mysql uv run pytest
```

These same checks run in CI (`.github/workflows/ci.yml`) and must all
pass before a PR is mergeable:

- **ruff**: lint and formatting
- **mypy** (`strict = true`, with `django-stubs`): typing must stay
  precise, including on code touching the ORM and Django signals
- **pytest**: on the three supported databases (SQLite, PostgreSQL,
  MySQL) and against Django 4.2/5.0/5.1/5.2 (SQLite). The suite covers
  the five write backends (`sync`, `on_commit`, `thread`, `asyncio`,
  `celery`), the diff engine, the decorator, the DRF mixin, the Admin,
  and the `django-signals-all` integration. Coverage is locked at 100%
  (`--cov-fail-under=100` via `[tool.coverage.report]`): any new code
  branch must be tested.

If `pre-commit` is installed (`uv run pre-commit install`), ruff and
mypy run automatically before each commit.

## Compatibility

`django-forge-log` targets **Python 3.12+** and **Django 4.2+**
(current LTS and later versions). Any PR must remain compatible with
these minimum versions; do not introduce an implicit dependency on a
newer version without discussing it in an issue first.

## Code style

- No comments explaining the *what* (the code should be readable on
  its own) — only the *why* when it's not obvious (hidden constraints,
  undocumented Django behavior, a workaround for a known bug).
- No abstraction or feature added beyond what the change requires.
- The core (`forge_log.decorators`, `forge_log.middleware`,
  `forge_log.admin`, `forge_log.models`) must never depend on DRF or
  `django-signals-all` — those integrations stay in `forge_log.drf` and
  `forge_log.signals_integration`, loaded as extras (`[drf]`,
  `[signals]`). A direct `import` of `rest_framework`/
  `django_signals_all` outside of these two modules is a regression.
- Any new field logged by default (diff, request context) must be run
  through the Security/PII section of the README before being merged:
  a sensitive field leaking into `ActionLog.changes` is a high-severity
  bug, not an implementation detail.

## Commits and PRs

- A clear commit message that explains the *why* of the change.
- One PR = one topic. Prefer several small PRs over one catch-all PR.
- Describe in the PR description what changes and how it's tested.

## Compatibility and deprecation policy

`django-forge-log` follows [Semantic Versioning](https://semver.org/).
The project is currently in the *release candidate* phase
(`1.0.0rcN`): the API is considered frozen but has not yet been
exercised by real-world usage outside of this repository — see the
[release candidate policy](RELEASING.md#release-candidate-policy-before-the-final-100)
in RELEASING.md for what can/cannot change from one RC to the next.

Starting from `1.0.0`:

- a **major** (`X.0.0`) can break compatibility;
- a **minor** (`1.X.0`) adds features without breaking anything;
- a **patch** (`1.0.X`) contains only bug fixes.

After `1.0.0`, any deprecated public API keeps working and raises an
explicit `DeprecationWarning` for at least one full minor version
before being removed in a later major version.

## Reporting a bug or proposing a feature

Open an [issue](https://github.com/alzeph/django-forge-log/issues)
using the appropriate template. For a security vulnerability, see
[SECURITY.md](SECURITY.md) instead of a public issue.
