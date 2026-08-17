# Release process

*English | [Français](RELEASING.fr.md)*

This document describes how to publish a new version of
`django-forge-log` to PyPI. It's intended for anyone with the
necessary rights on the repository (not just the original maintainer):
following these steps in order should be enough, with no implicit
knowledge of the project beyond what's written here.

## Who can publish

- Write access to the `alzeph/django-forge-log` GitHub repository (to
  create a branch, a tag, and push to `main`).
- Rights to create/approve a
  [GitHub Release](https://github.com/alzeph/django-forge-log/releases).
  If the `pypi` environment (see below) has reviewers configured, their
  approval is required before `publish.yml` runs.
- No personal PyPI account is required to publish once *trusted
  publishing* is configured (see below): authorization goes through
  OIDC, not an individual token.

## Initial PyPI setup (already done for this repository)

`django-forge-log` publishes via PyPI's *trusted publishing* (OIDC): no
long-lived token to manage, authorization is tied to this exact
repository and this exact GitHub Actions workflow. Configured and
verified by successfully publishing `1.0.0rc1` and `1.0.0rc2` — the
steps below only need to be redone if the repository is
renamed/moved, or if the trusted publisher is revoked.

1. Create a PyPI account if needed.
2. On <https://pypi.org/manage/account/publishing/>, add a *pending
   trusted publisher* (the project doesn't need to already exist on
   PyPI):
   - PyPI project name: `django-forge-log`
   - Owner: `alzeph`
   - Repository name: `django-forge-log`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
3. In the repository's GitHub settings (`Settings > Environments`),
   create a `pypi` environment (protects the publish step, allows
   adding reviewers if needed).

## Publishing a version

### 1. Choose the version number

While the project is in the *release candidate* phase (`1.0.0rcN`, the
current situation), see the
[Release candidate policy](#release-candidate-policy-before-the-final-100)
section below to decide whether to bump `N` (`rc2` → `rc3`) or tag the
final `1.0.0`.

Once `1.0.0` is tagged, follow standard
[Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`) — see
the
[Compatibility policy](CONTRIBUTING.md#compatibility-and-deprecation-policy)
section of CONTRIBUTING.md if in doubt about the bump type.

### 2. Prepare a release branch

Don't commit directly to `main`. Create a dedicated branch:

```bash
git checkout -b release/X.Y.Z
```

On this branch:

1. Update `__version__` in `src/forge_log/__init__.py` (the package
   version is single-sourced from this file, see
   `[tool.hatch.version]` in `pyproject.toml`).
2. Move the content of `## [Unreleased]` into `CHANGELOG.md` **and**
   `CHANGELOG.fr.md` under a new `## [X.Y.Z] - YYYY-MM-DD` section, and
   update the comparison links at the bottom of each file.

### 3. Verify locally

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy
uv run pytest --cov=forge_log --cov-report=term-missing
uv build
```

For any change touching `ActionLog`, the diff engine, or the writers,
also verify against PostgreSQL and MySQL — correct behavior under
SQLite can crash elsewhere (strict `varchar(n)`, `inet` column...),
and CI is the only place that would otherwise catch it:

```bash
docker compose up -d
FORGE_LOG_TEST_DB=postgres uv run pytest
FORGE_LOG_TEST_DB=mysql uv run pytest
docker compose down
```

All these commands must pass before continuing. They match exactly
what CI (`.github/workflows/ci.yml`) re-checks on the PR — the
`test (sqlite|postgres|mysql)` matrix in particular has already caught
a test bug that passed locally (on SQLite) but not in CI (see
`CHANGELOG.md`, `1.0.0rc2`).

### 4. Open a PR and merge

```bash
git add -A
git commit -m "Release X.Y.Z"
git push -u origin release/X.Y.Z
gh pr create --base main --title "Release X.Y.Z" --body "See CHANGELOG.md"
```

Wait for CI to pass on the PR, then merge into `main`.

### 5. Tag

Switch back to an up-to-date `main`, then create an **annotated tag**
(carries a message and an author, unlike a lightweight tag — this is
the standard practice for marking a release):

```bash
git checkout main
git pull origin main
git tag -a vX.Y.Z -m "Release X.Y.Z"
git push origin vX.Y.Z
```

### 6. Create the GitHub Release

Create a [GitHub Release](https://github.com/alzeph/django-forge-log/releases/new)
from the `vX.Y.Z` tag, with release notes taken from `CHANGELOG.md`.
Publishing it triggers `.github/workflows/publish.yml`, which builds
and publishes automatically to PyPI.

- Before `1.0.0`, checking **"Set as a pre-release"** is optional but
  recommended to signal the lack of API stability guarantees.
- Then verify that the `publish` job of
  `.github/workflows/publish.yml` completes successfully (`gh run
  watch` or the repository's Actions tab) and that the version appears
  on <https://pypi.org/project/django-forge-log/>.

## Release candidate policy before the final 1.0.0

`1.0.0rc1`/`rc2`/`rc3` are successive *release candidates*: the API is
considered frozen but has not yet been exercised by real-world usage
outside of this repository. Before tagging `1.0.0` (final):

- leave the current RC available for at least a few weeks to gather
  feedback (issues, real use cases, bugs);
- if a bug is found, publish a new RC (`rcN+1`) rather than modifying
  an already-published RC after the fact — every PyPI tag/release is
  immutable;
- an RC can contain either only fixes (`1.0.0rc1` → `1.0.0rc2`, five
  robustness bugs, no API change) or new features that round out the
  API before it's frozen for good (`1.0.0rc2` → `1.0.0rc3`) — both are
  legitimate as long as the final `1.0.0` hasn't been tagged;
- an API change between two RCs must be documented in `CHANGELOG.md`
  (`### Changed`/`### Added`/`### Removed` section as appropriate), the
  RC remaining by nature a pre-version with no stability guarantee.

Once `1.0.0` is tagged, see the compatibility policy in
[CONTRIBUTING.md](CONTRIBUTING.md#compatibility-and-deprecation-policy)
— no more breaking changes outside of a `MAJOR` bump.
