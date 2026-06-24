"""Tests de non-régression du script d'assemblage build_index.py.

Couvre les deux points sensibles identifiés par l'audit de sécurité :
la validation anti path-traversal des fragments et la transformation
de production (suppression du CDN Tailwind et nettoyage de la CSP).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import build_index

# ---------------------------------------------------------------------------
# Validation des chemins de fragments (anti path traversal)
# ---------------------------------------------------------------------------


def test_valider_chemin_fragment_accepte_chemin_partials() -> None:
    """Un fragment situé sous partials/ est accepté sans exception."""
    build_index.valider_chemin_fragment("partials/header.html")


@pytest.mark.parametrize(
    "chemin_interdit",
    [
        "partials/../scripts/build_index.py",
        "partials/../../secrets.txt",
        "partials\\..\\index.template.html",
        "../partials/header.html",
    ],
)
def test_valider_chemin_fragment_rejette_traversal(chemin_interdit: str) -> None:
    """Toute tentative de remontée hors de partials/ est rejetée."""
    with pytest.raises(ValueError):
        build_index.valider_chemin_fragment(chemin_interdit)


@pytest.mark.parametrize(
    "chemin_hors_dossier",
    ["scripts/build_index.py", "index.html", "css/styles.css"],
)
def test_valider_chemin_fragment_rejette_hors_partials(
    chemin_hors_dossier: str,
) -> None:
    """Un chemin hors du dossier partials/ est rejeté."""
    with pytest.raises(ValueError):
        build_index.valider_chemin_fragment(chemin_hors_dossier)


# ---------------------------------------------------------------------------
# Assemblage des fragments
# ---------------------------------------------------------------------------


def test_assembler_page_remplace_directives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Chaque directive @partial est remplacée par le contenu du fragment."""
    (tmp_path / "partials").mkdir()
    (tmp_path / "partials" / "bloc.html").write_text(
        "<p>Contenu du bloc</p>\n", encoding="utf-8"
    )
    monkeypatch.setattr(build_index, "ROOT_DIR", tmp_path)

    resultat = build_index.assembler_page(
        "<body>\n<!-- @partial partials/bloc.html -->\n</body>"
    )

    assert "<p>Contenu du bloc</p>" in resultat
    assert "@partial" not in resultat


def test_assembler_page_traite_fragment_imbrique(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Un fragment contenant lui-même une directive est résolu en cascade."""
    partials = tmp_path / "partials"
    partials.mkdir()
    (partials / "parent.html").write_text(
        "<div><!-- @partial partials/enfant.html --></div>", encoding="utf-8"
    )
    (partials / "enfant.html").write_text("<span>ok</span>", encoding="utf-8")
    monkeypatch.setattr(build_index, "ROOT_DIR", tmp_path)

    resultat = build_index.assembler_page(
        "<!-- @partial partials/parent.html -->"
    )

    assert resultat == "<div><span>ok</span></div>"


def test_lire_fragment_introuvable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Un fragment absent lève FileNotFoundError avec un message actionnable."""
    (tmp_path / "partials").mkdir()
    monkeypatch.setattr(build_index, "ROOT_DIR", tmp_path)

    with pytest.raises(FileNotFoundError):
        build_index.lire_fragment("partials/absent.html")


# ---------------------------------------------------------------------------
# Transformation de production (--prod)
# ---------------------------------------------------------------------------

HEAD_DEV = """<head>
    <meta http-equiv="Content-Security-Policy" content="default-src 'self' file:; \
style-src 'self' file: 'unsafe-inline'; script-src 'self' file: \
https://cdn.tailwindcss.com; connect-src 'self' file: https://cdn.tailwindcss.com;">

    <!-- Tailwind CSS (CDN) + configuration locale -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="js/tailwind.config.js"></script>
</head>"""


def test_optimisations_production_remplacent_le_cdn() -> None:
    """Le bloc CDN Tailwind est remplacé par le CSS compilé statique."""
    resultat = build_index.appliquer_optimisations_production(HEAD_DEV)

    assert 'href="css/tailwind.built.css"' in resultat
    assert "cdn.tailwindcss.com" not in resultat
    assert '<script src="js/tailwind.config.js">' not in resultat


def test_optimisations_production_nettoient_la_csp() -> None:
    """La CSP <meta> de production ne référence plus ni le CDN ni file:."""
    resultat = build_index.appliquer_optimisations_production(HEAD_DEV)

    assert "script-src 'self';" in resultat
    assert "connect-src 'self';" in resultat
    assert "cdn.tailwindcss.com" not in resultat
    assert "file:" not in resultat


def test_optimisations_production_sans_bloc_cdn() -> None:
    """Un contenu déjà propre ressort inchangé (idempotence)."""
    contenu = "<head><link rel=\"stylesheet\" href=\"css/styles.built.css\"></head>"

    assert build_index.appliquer_optimisations_production(contenu) == contenu
