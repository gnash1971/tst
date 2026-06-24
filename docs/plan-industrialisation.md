# Plan d'industrialisation — Lentilly Tennis de Table

- **Projet** : site documentaire statique `clubTTLentilly`
- **Date** : 24 juin 2026
- **Statut** : plan **revu et corrigé** après vérification de pré-vol sur le
  code réel (en attente de feu vert pour implémentation)
- **Profil retenu** : dépôt **public**, mainteneur **solo**, ambition
  **minimaliste**
- **Objectifs prioritaires** : **fiabilité / zéro régression**,
  **performance · SEO · accessibilité** du site public, **sécurité &
  conformité**

---

## 0. Étape préalable obligatoire — remise au propre du code

> ⚠️ **À faire AVANT de rendre `ruff` bloquant en CI.** La vérification de
> pré-vol a montré que le code n'est pas conforme à la configuration `ruff`
> existante (voir § 1). Activer un job bloquant sans cette étape rendrait la
> **toute première exécution de CI rouge**.

1. Corriger l'auto-réparable : `ruff check --fix` (résout `UP007`, `I001`) puis
   `ruff format` (8 fichiers à reformater).
2. Traiter les `E501` résiduels (commentaires, docstrings, regex : **non**
   reformatés automatiquement) par un retour à la ligne manuel ou un
   `# noqa: E501` ciblé et justifié.
3. Déclarer les modules internes pour l'ordre des imports, sinon `I001`
   persiste sur les tests :

   ```toml
   [tool.ruff.lint.isort]
   known-first-party = ["build_index", "build_dist", "models"]
   ```

> `mypy --strict` passe déjà : **aucune** remédiation de typage nécessaire.

---

## 1. Synthèse de l'état actuel

Le site est déjà très bien outillé pour un mini-site statique :

- **Build reproductible et piloté par les données** : `data/documents.json`
  validé par Pydantic → gabarits Jinja2 → `scripts/build_index.py --prod` →
  Tailwind (`build:css`) → `scripts/build_dist.py` (dossier `dist/` épuré).
- **Thème centralisé** : `data/brand-theme.json` comme source unique.
- **Assets optimisés** : images responsives WebP/AVIF versionnées, service
  worker hors-ligne (`sw.js`).
- **Qualité configurée** : `pytest` (4 fichiers), `mypy --strict`, `ruff`,
  `pip-audit` déclarés dans `pyproject.toml`.
- **Dépendances maîtrisées** : `uv` + `uv.lock` + export `requirements.txt`.
- **Sécurité & SEO** : `_headers` (CSP stricte, HSTS…), `.htaccess`,
  `sitemap.xml`, `robots.txt`, `site.webmanifest`.
- **Gouvernance** : `README`, `CONTRIBUTING`, `CODE_OF_CONDUCT`, `SECURITY`,
  templates d'issues.

### Constat structurant

Toute la garantie qualité repose sur `publier_git.bat`, qui est :

1. **Non versionné** : ignoré par Git (comme `scripts/git_commit_message.ps1`).
2. **Windows-only** (script `cmd`).
3. **Incomplet** : il exécute uniquement `npm run build` + `pytest`, mais
   **ni `ruff`, ni `mypy`, ni `pip-audit`** (pourtant tous configurés).

### Résultats de la vérification de pré-vol (faits mesurés)

Outils exécutés localement sur le code réel (`uv` 0.11, Python 3.12) :

| Contrôle | Résultat | Conséquence pour le plan |
|---|---|---|
| `ruff check` | **18 erreurs** (`E501` ×13, `UP007` ×1, `I001` ×4) | Étape 0 obligatoire |
| `ruff format --check` | **8 fichiers** à reformater | Étape 0 obligatoire |
| `mypy --strict` | **OK** (17 fichiers) | Étape mypy sûre |
| `pytest` | **62 tests verts** (exit 0) | Suite saine |
| Couverture | **25 %** global ; **≈ 77 %** sur le périmètre critique | Restreindre le périmètre ; seuil de départ 75 % |

> Conclusion : le diagnostic du plan (outils configurés mais **non appliqués**)
> est **prouvé** — le code a dérivé hors des règles `ruff` faute d'exécution.

---

## 2. Principe directeur

Le vrai gain n'est pas d'ajouter des outils (ils existent déjà), mais de **les
exécuter automatiquement et de façon partagée**, via une **CI versionnée et
multiplateforme**, avec **une source unique de vérité** entre l'exécution
locale et l'intégration continue.

La contrainte « minimaliste » est conciliée avec les objectifs perf/SEO/a11y et
sécurité grâce à **un seul workflow** dont les contrôles « web » s'exécutent
contre le `dist/` déjà construit (servi localement par le runner) : aucune
infrastructure externe, aucun secret Netlify. Le dépôt étant public, GitHub
Actions est gratuit et illimité.

---

## 3. Plan finalisé

### 3.1. Source unique de vérité local ↔ CI

Scripts `npm` partagés, appelés à la fois en local et par la CI. **Important :
`build` reste en `python` nu** car il est aussi exécuté par Netlify, qui n'a
pas `uv` ; seuls les outils de dev passent par `uv run`. On sépare donc
`verify` (contrôles, **sans** build) de `build`.

```json
"scripts": {
  "lint": "uv run ruff check . && uv run ruff format --check .",
  "typecheck": "uv run mypy",
  "test": "uv run pytest --cov=build_index --cov=build_dist --cov=models --cov-report=term-missing --cov-fail-under=75",
  "audit": "uv run pip-audit",
  "verify": "npm run lint && npm run typecheck && npm run test && npm run audit",
  "check": "npm run verify && npm run build"
}
```

- `publier_git.bat` appelle **`npm run verify`** (et **non** `check`) à l'étape
  des tests (Step 03b) : il conserve ainsi son propre build de prod (Step 03)
  et la régénération `dev` de `index.html` (Step 04), sans double build ni
  perturbation de l'ordre prod→dev.
  *Note : `publier_git.bat` étant gitignoré, cette modification reste locale.*
- Seuil de couverture : **mesuré à ≈ 77 %** sur le périmètre
  `build_index`/`build_dist`/`models` (`models` 99 %, `build_dist` 74 %,
  `build_index` 62 %). Démarrer à **75 %** (marge de sécurité), puis remonter
  par paliers (« ratchet ») vers 90 % en couvrant les zones manquantes (§ 3.4).
- Ajout d'un **`.nvmrc`** (Node 20) lu en local, en CI et par Netlify.
- `uv run` suppose l'environnement synchronisé (`uv sync --extra dev`) ; sur
  Google Drive, utiliser `UV_PROJECT_ENVIRONMENT` hors dossier synchronisé
  (cf. README).

### 3.2. Parité Netlify + détection de dérive du lock

1. **Build identique à la production** (sans `uv`, sans `npm ci`) — Tailwind
   est déjà épinglé via `npx`, donc l'exécution est strictement la même qu'en
   local :

   ```bash
   pip install -r requirements.txt && npm run build
   ```

2. **Garde anti-dérive du lock** (cohérente avec le pattern existant
   `test_config_cdn_synchronisee_avec_theme`) : échoue si `requirements.txt`
   est périmé vis-à-vis de `uv.lock` :

   ```bash
   uv export --no-dev --frozen -o requirements.txt
   git diff --exit-code -- requirements.txt
   ```

   Cette garde reste pleinement compatible avec l'**option C** de Dependabot
   (§ 3.6), où les dépendances Python sont mises à jour manuellement.

### 3.3. Workflow CI unique : `.github/workflows/ci.yml`

Déclenché sur `push` et `pull_request`, en **deux jobs** (une seule pile, sans
mélanger l'environnement outils-dev `uv` et l'environnement prod `pip`).

**Job `qualite`** (environnement `uv`) — **bloquant** :

- `ruff check` + `ruff format --check`
- `mypy` (strict, déjà vert)
- `pytest` + **couverture restreinte** au chemin de déploiement
  (`build_index`, `build_dist`, `models`) — cf. § 3.4
- `uv run pip-audit` (**environnement complet**, dev inclus — et non seulement
  les 2 deps de `requirements.txt`)
- **garde anti-dérive du lock** (§ 3.2)

**Job `build-web`** (environnement « prod », parité Netlify) :

- `pip install -r requirements.txt && npm run build` (**pas** de `npm ci`)
- Sur le `dist/` produit — **Couche « qualité web », d'abord informative**
  (rapport non bloquant, durcie une fois les seuils calibrés) :
  - **Lighthouse CI** (`staticDistDir: ./dist`) — budgets Perf/SEO/A11y/Best
  - **Validation HTML** des `dist/**/*.html`
  - **Liens morts** (lychee) **limités aux liens internes** (les externes sont
    écartés pour éviter une CI *flaky* ; activables au besoin)

### 3.4. Couverture de tests : périmètre réaliste

Les 9 scripts de génération d'assets (`generate_images`, `gen_og_image`,
`gen_favicons`, `download_fonts`, `extract_logo`, `replace_logo`, `fix_mime`,
`gen_qr_flyer`, `_gen_qr_flyer`) sont de l'**outillage manuel** (Pillow,
qrcode), non testé et sans vocation à l'être. Mesurer la couverture sur tout
`scripts/` produirait un seuil ingérable.

→ Restreindre la mesure au **chemin critique de déploiement**, via les options
`--cov=build_index --cov=build_dist --cov=models` du script `test` (§ 3.1)
**ou** — de façon équivalente et exclusive — via `pyproject.toml` :

```toml
[tool.coverage.run]
source = ["build_index", "build_dist", "models"]
```

Ajouter `pytest-cov` au groupe `dev` de `pyproject.toml`.

**Mesure actuelle sur ce périmètre : ≈ 77 %** (`models.py` 99 %,
`build_dist.py` 74 %, `build_index.py` 62 %). Les manques principaux sont
l'assemblage CSS (`assembler_styles_production`) et le point d'entrée `main()`
de `build_index.py` (lignes ~230-308). Pour viser 90 %, ajouter des tests sur
ces deux zones et sur les quelques branches non couvertes de `build_dist.py`.

### 3.5. Garde-fous « en dépôt » (testables localement, donc en CI)

- **Test d'intégrité de `_headers`** : présence des directives clés (CSP
  `default-src 'self'`, `X-Content-Type-Options: nosniff`, HSTS…) et copie dans
  `dist/`. Empêche une régression silencieuse de la posture sécurité.
- **Test de cohérence de version** : échoue si `package.json` et
  `pyproject.toml` divergent (tous deux à `1.0.0` aujourd'hui).
- **Compléter `tests/test_build_dist.py`** si besoin : présence des `<picture>`,
  du service worker et des partials dans `dist/`.

### 3.6. Dépendances : `.github/dependabot.yml` — **option C**

Surveillance limitée à **`npm`** (Tailwind) et **`github-actions`**, en PR
hebdomadaires.

> **Pourquoi pas l'écosystème `uv` ?** Dependabot traite `pyproject.toml` +
> `uv.lock` comme sources de vérité et **ne régénère pas** `requirements.txt` ;
> ses PR feraient donc échouer la garde anti-dérive (§ 3.2). Les 2 deps Python
> de prod (`jinja2`, `pydantic`) étant **stables**, on les met à jour
> **manuellement** (la garde + `pip-audit` servant de filets). C'est le choix
> le plus cohérent avec un profil minimaliste/solo.
>
> Alternatives écartées ici : **A** (étape CI qui régénère et recommit
> `requirements.txt` sur les PR Dependabot) ; **B** (ne plus committer
> `requirements.txt`, l'exporter au build Netlify, faisant de `uv.lock` la
> source unique). À reconsidérer si les deps Python se multiplient.

---

## 4. Ce qui est délibérément écarté

Cohérent avec un profil **minimaliste + solo** ; à reconsidérer si le contexte
évolue (équipe, produit critique) :

- Releases / `CHANGELOG` automatisés, tags sémantiques.
- Monitoring d'uptime, reporting d'erreurs JavaScript.
- Template de Pull Request, *Conventional Commits* imposés.
- Renovate (Dependabot suffit) et l'auto-mise à jour des deps **Python**
  (option C : manuelle).
- Protection de branche stricte (peu utile en solo ; *required checks*
  activables comme auto-discipline).

---

## 5. Fichiers concernés

| Fichier | Action |
|---|---|
| `scripts/*.py`, `tests/*.py` | **corriger** (Étape 0 : `ruff --fix` + format + `E501`) |
| `.github/workflows/ci.yml` | créer (2 jobs : `qualite` + `build-web`) |
| `.github/dependabot.yml` | créer (npm + github-actions) |
| `.nvmrc` | créer (Node 20) |
| `lighthouserc.json` | créer (config Lighthouse CI) |
| `package.json` | modifier (scripts `lint`/`typecheck`/`test`/`audit`/`verify`/`check`) |
| `pyproject.toml` | modifier (`pytest-cov`, `known-first-party`, périmètre de couverture) |
| `publier_git.bat` | modifier (appel `npm run verify`) — *local, non versionné* |
| `tests/` | ajouter tests `_headers` + cohérence de version |

---

## 6. Ordre de mise en œuvre

0. **Remise au propre `ruff`** (§ 0) + config `known-first-party`.
1. **Socle local ↔ CI** : scripts `npm` (`verify`/`check`) + `.nvmrc` + mise à
   jour `publier_git.bat`.
2. **Couverture & garde-fous** : `pytest-cov` + `[tool.coverage.run]`, tests
   `_headers` + cohérence de version ; seuil de départ **75 %** (mesuré ≈ 77 %),
   ratchet vers 90 %.
3. **CI job `qualite`** (bloquant) + garde anti-dérive du lock.
4. **CI job `build-web`** (parité Netlify, sans `npm ci`) + Couche qualité web
   informative + `lighthouserc.json`.
5. **`dependabot.yml`** (option C).

---

## 7. Journal des décisions (arbitrages de cadrage)

| Décision | Choix retenu | Raison |
|---|---|---|
| Périmètre CI | Un seul workflow, 2 jobs | Minimalisme, sans mélange d'environnements |
| Pré-requis | Étape 0 de remise au propre `ruff` | Pré-vol : 18 erreurs + 8 fichiers non formatés |
| Validation build | Commande Netlify exacte, **sans `npm ci`** | Tailwind déjà épinglé via `npx` = vraie parité |
| Dérive du lock | `uv export --frozen` + `git diff --exit-code` | Empêcher un `requirements.txt` périmé |
| Dépendances | **Dependabot npm + actions** ; Python manuel | Éviter le conflit Dependabot `uv` ⨯ garde du lock |
| Couverture | Restreinte à `build_index`/`build_dist`/`models` | Les scripts d'assets ne sont pas testables utilement |
| Seuil couverture | Mesuré ≈ 77 % ; départ **75 %**, ratchet → 90 % | Éviter une CI rouge dès le 1er jour |
| `pip-audit` | Environnement complet (`uv run pip-audit`) | Auditer aussi les outils dev, pas seulement la prod |
| Scripts npm | `verify` (sans build) séparé de `build` | `build` partagé avec Netlify (sans `uv`) |
| Lighthouse | Lighthouse CI sur `dist/` local | Pas de secret/preview Netlify requis |
| Liens morts | Internes uniquement (par défaut) | Éviter une CI *flaky* sur sites tiers |
| Couche qualité web | Informative d'abord | Pas de friction avant calibrage des seuils |
