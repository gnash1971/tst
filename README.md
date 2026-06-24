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

### Contenu documentaire (cartes)

Les cartes de la page d'accueil sont générées depuis `data/documents.json`
(validé par Pydantic, voir `scripts/models.py`) via le gabarit
`templates/doc-card.html.j2`. Pour ajouter ou modifier une carte : éditer
`data/documents.json` puis régénérer (`python scripts/build_index.py`).

### Thème Tailwind

Source unique : `data/brand-theme.json` (couleurs de marque + polices).
`tailwind.config.js` (CLI) la charge via `require` ; `js/tailwind.config.js`
(Play CDN, mode dev) est **régénéré au build** par `scripts/build_index.py`.

### Images responsives (WebP / AVIF)

Les variantes responsives des logos et visuels sont produites par
`scripts/generate_images.py` (Pillow) puis **versionnées** (Netlify n'a donc
pas besoin de Pillow). À relancer lorsqu'une image source change :

```bash
python scripts/generate_images.py          # idempotent (ne refait que le nécessaire)
python scripts/generate_images.py --force   # tout régénérer
```

Les pages servent ces images via `<picture>` (AVIF, puis WebP, puis PNG de
repli) avec `srcset`/`sizes` adaptés ; les logos sous la ligne de flottaison
(footer, filigrane) sont en `loading="lazy"`.

### Service worker

`sw.js` (cache hors-ligne) est enregistré par `js/ltt-sw-register.js`
uniquement en `https`/`localhost`. Incrémenter `VERSION` dans `sw.js` pour
invalider l'ancien cache lors d'un changement majeur d'assets.

### Analytics (mesure d'audience)

L'audience est mesurée via **Netlify Analytics** (côté serveur, basé sur les
logs du CDN) : aucun script, aucun cookie, aucun bandeau RGPD et **aucun
impact sur la CSP**. Rien à installer dans le dépôt.

- **Activation** : tableau de bord Netlify → *Site* → onglet **Analytics** →
  *Enable* (fonctionnalité payante, par site).
- **Ce que l'on suit** : pages et ressources les plus consultées. Les documents
  étant de vraies pages/fichiers (`fic/*.html`, `pub/flyerA5.pdf`, visuels),
  ils apparaissent dans les *Top pages* / *Top resources* — d'où la
  fréquentation réelle de chaque document, sans traceur côté client.

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
