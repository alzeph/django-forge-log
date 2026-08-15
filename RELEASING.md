# Process de release

Ce document décrit comment publier une nouvelle version de
`django-forge-log` sur PyPI. Il s'adresse à toute personne ayant les droits
nécessaires sur le dépôt (pas seulement au mainteneur d'origine) : suivre
ces étapes dans l'ordre doit suffire, sans connaissance implicite du projet
au-delà de ce qui est écrit ici.

## Qui peut publier

- Un accès en écriture sur le dépôt GitHub `alzeph/django-forge-log` (pour
  créer une branche, un tag, et pousser sur `main`).
- Les droits pour créer/approuver une
  [GitHub Release](https://github.com/alzeph/django-forge-log/releases). Si
  l'environnement `pypi` (voir plus bas) a des reviewers configurés, leur
  approbation est nécessaire avant que `publish.yml` ne s'exécute.
- Aucun compte PyPI personnel n'est requis pour publier une fois le
  *trusted publishing* configuré (voir ci-dessous) : l'autorisation passe
  par OIDC, pas par un token individuel.

## Configuration initiale de PyPI (à faire une fois pour ce dépôt)

`django-forge-log` publie via le *trusted publishing* de PyPI (OIDC) :
aucun token long-lived à gérer, l'autorisation est liée à ce dépôt et à ce
workflow GitHub Actions précis. Tant que cette configuration n'est pas
faite, `publish.yml` échouera à l'étape de publication.

1. Créer un compte PyPI si besoin.
2. Sur <https://pypi.org/manage/account/publishing/>, ajouter un
   *pending trusted publisher* (le projet n'a pas besoin d'exister sur PyPI
   au préalable) :
   - PyPI project name : `django-forge-log`
   - Owner : `alzeph`
   - Repository name : `django-forge-log`
   - Workflow name : `publish.yml`
   - Environment name : `pypi`
3. Dans les paramètres GitHub du dépôt (`Settings > Environments`), créer
   un environnement `pypi` (protège la publication, permet d'ajouter des
   reviewers si besoin).

Cette configuration n'est à refaire que si le dépôt est renommé/déplacé, ou
si le trusted publisher est révoqué.

## Publier une version

### 1. Choisir le numéro de version

Suivre le [Semantic Versioning](https://semver.org/lang/fr/) :
`MAJOR.MINOR.PATCH`. En cas de doute sur le type de bump, se référer à la
section [Politique de compatibilité](CONTRIBUTING.md#politique-de-compatibilité-et-dépréciation)
de CONTRIBUTING.md — avant `1.0.0`, aucune garantie de stabilité d'API
n'est donnée, donc un `0.x` mineur peut casser la compatibilité s'il le
documente.

### 2. Préparer une branche de release

Ne pas committer directement sur `main`. Créer une branche dédiée :

```bash
git checkout -b release/X.Y.Z
```

Sur cette branche :

1. Mettre à jour `__version__` dans `src/forge_log/__init__.py` (la version
   du package est single-sourcée depuis ce fichier, voir
   `[tool.hatch.version]` dans `pyproject.toml`).
2. Déplacer le contenu de `## [Unreleased]` dans `CHANGELOG.md` sous une
   nouvelle section `## [X.Y.Z] - AAAA-MM-JJ`, et mettre à jour les liens
   de comparaison en bas de fichier.

### 3. Vérifier localement

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy
uv run pytest --cov=forge_log --cov-report=term-missing
uv build
```

Toutes ces commandes doivent passer avant de continuer. Elles correspondent
exactement à ce que la CI (`.github/workflows/ci.yml`) revérifie sur la PR.

### 4. Ouvrir une PR et merger

```bash
git add -A
git commit -m "Release X.Y.Z"
git push -u origin release/X.Y.Z
gh pr create --base main --title "Release X.Y.Z" --body "Voir CHANGELOG.md"
```

Attendre que la CI passe sur la PR, puis merger dans `main`.

### 5. Tagger

Se remettre sur `main` à jour, puis créer un **tag annoté** (porte un
message et un auteur, contrairement à un tag léger — c'est la pratique
standard pour marquer une release) :

```bash
git checkout main
git pull origin main
git tag -a vX.Y.Z -m "Release X.Y.Z"
git push origin vX.Y.Z
```

### 6. Créer la GitHub Release

Créer une [GitHub Release](https://github.com/alzeph/django-forge-log/releases/new)
à partir du tag `vX.Y.Z`, avec les notes de version reprises de
`CHANGELOG.md`. La publier déclenche `.github/workflows/publish.yml`, qui
build et publie automatiquement sur PyPI.

- Avant `1.0.0`, cocher **"Set as a pre-release"** est optionnel mais
  recommandé pour signaler l'absence de garantie de stabilité de l'API.
- Vérifier ensuite que le job `publish` de `.github/workflows/publish.yml`
  se termine avec succès (`gh run watch` ou l'onglet Actions du dépôt) et
  que la version apparaît sur <https://pypi.org/project/django-forge-log/>.
