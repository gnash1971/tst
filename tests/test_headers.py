"""Tests de la posture de sécurité véhiculée par le fichier _headers.

Garantit que les en-têtes de sécurité essentiels (CSP, HSTS, anti-sniffing…)
restent présents et que ce fichier est bien publié dans dist/.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import build_dist

# Fichier _headers réel, à la racine du dépôt.
HEADERS_PATH = Path(__file__).resolve().parent.parent / "_headers"


def _contenu_headers() -> str:
    """Retourne le contenu du fichier _headers réel."""
    return HEADERS_PATH.read_text(encoding="utf-8")


def test_headers_present() -> None:
    """Le fichier _headers existe à la racine du dépôt."""
    assert HEADERS_PATH.is_file()


@pytest.mark.parametrize(
    "directive",
    [
        "Content-Security-Policy:",
        "default-src 'self'",
        "X-Content-Type-Options: nosniff",
        "X-Frame-Options: DENY",
        "Referrer-Policy:",
        "Permissions-Policy:",
        "Cross-Origin-Opener-Policy: same-origin",
        "Strict-Transport-Security:",
        "includeSubDomains",
    ],
)
def test_headers_contient_directive_securite(directive: str) -> None:
    """Chaque en-tête de sécurité essentiel est présent dans _headers."""
    assert directive in _contenu_headers()


def test_headers_csp_verrouille_les_sources_sensibles() -> None:
    """La CSP interdit les sources dangereuses (objets, base-uri, cadrage)."""
    contenu = _contenu_headers()
    assert "object-src 'none'" in contenu
    assert "base-uri 'none'" in contenu
    assert "frame-ancestors 'none'" in contenu


def test_headers_publie_dans_dist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """build_dist copie _headers dans dist/ (publication de la posture)."""
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / "_headers").write_text(
        "/*\n  X-Frame-Options: DENY\n", encoding="utf-8"
    )
    dist = tmp_path / "dist"
    monkeypatch.setattr(build_dist, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(build_dist, "DIST_DIR", dist)

    build_dist.preparer_dossier_production()

    assert (dist / "_headers").is_file()
