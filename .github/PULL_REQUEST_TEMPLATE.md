## What and why

## How it's tested

## Checklist

- [ ] `uv run ruff check src tests` and `uv run ruff format --check src tests`
- [ ] `uv run mypy`
- [ ] `uv run pytest --cov=forge_log --cov-report=term-missing`
- [ ] `CHANGELOG.md` (and `CHANGELOG.fr.md`) updated if public behavior changes
