# Portail documentaire — Lentilly Tennis de Table

Mini-site statique des documents officiels du club (inscription, règlement, statuts, PV).

Les droits sur le code et les documents sont précisés dans [LICENSE](LICENSE).

## Développement

Prérequis : Python 3.12+, Node.js et [uv](https://docs.astral.sh/uv/).

```bash
# Installer les dépendances (build + outils de dev) dans un environnement virtuel
uv sync --extra dev

# Lancer les tests
uv run pytest

# Construire le site de production (génère dist/)
uv run npm run build
```

> Sur Google Drive, si `uv sync` échoue (mêmes limites d'écriture que
> `node_modules`), créer l'environnement hors du dossier synchronisé via la
> variable `UV_PROJECT_ENVIRONMENT`.

### Dépendances

- **Build** — installées sur Netlify via `requirements.txt` (export figé de
  `uv.lock`) : `jinja2`, `pydantic`. L'environnement qui exécute `npm run build`
  doit pouvoir les importer.
- **Dev / génération d'assets** — groupe `dev` de `pyproject.toml` : `pytest`,
  `mypy`, `ruff`, `pip-audit`, `Pillow`, `qrcode`.

Après toute modification des dépendances dans `pyproject.toml`, régénérer le
lock et l'export Netlify :

```bash
uv lock
uv export --no-dev -o requirements.txt
```
