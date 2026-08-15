## Quoi et pourquoi

## Comment c'est testé

## Checklist

- [ ] `uv run ruff check src tests` et `uv run ruff format --check src tests`
- [ ] `uv run mypy`
- [ ] `uv run pytest --cov=forge_log --cov-report=term-missing`
- [ ] `CHANGELOG.md` mis à jour si le comportement public change
