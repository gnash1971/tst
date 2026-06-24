"""Tests de non-régression du script d'assemblage build_dist.py.

Garantit notamment que le dossier pub/ (visuels du club, ex. maillots)
est bien publié dans dist/, et que les exclusions restent appliquées.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import build_dist


@pytest.fixture()
def site_minimal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Construit une arborescence minimale du site dans un dossier temporaire."""
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / "robots.txt").write_text("User-agent: *\n", encoding="utf-8")
    (tmp_path / "sitemap.xml").write_text("<urlset></urlset>\n", encoding="utf-8")
    (tmp_path / "sw.js").write_text("/* sw */\n", encoding="utf-8")

    pub = tmp_path / "pub"
    pub.mkdir()
    (pub / "V5_t-shirts.png").write_bytes(b"png factice")

    css = tmp_path / "css"
    css.mkdir()
    (css / "styles.css").write_text("body {}", encoding="utf-8")
    (css / "tailwind-input.css").write_text("@tailwind;", encoding="utf-8")

    dist = tmp_path / "dist"
    monkeypatch.setattr(build_dist, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(build_dist, "DIST_DIR", dist)
    return dist


def test_preparer_dossier_production_publie_pub(site_minimal: Path) -> None:
    """Le dossier pub/ et son visuel sont copiés dans dist/."""
    build_dist.preparer_dossier_production()

    assert (site_minimal / "pub" / "V5_t-shirts.png").is_file()


def test_preparer_dossier_production_copie_les_requis(
    site_minimal: Path,
) -> None:
    """Les fichiers racine requis et le CSS public sont présents dans dist/."""
    build_dist.preparer_dossier_production()

    assert (site_minimal / "index.html").is_file()
    assert (site_minimal / "css" / "styles.css").is_file()


def test_preparer_dossier_production_exclut_tailwind_input(
    site_minimal: Path,
) -> None:
    """La source Tailwind d'entrée reste exclue de la publication."""
    build_dist.preparer_dossier_production()

    assert not (site_minimal / "css" / "tailwind-input.css").exists()


def test_preparer_dossier_production_publie_seo(site_minimal: Path) -> None:
    """Les fichiers SEO (robots.txt, sitemap.xml) sont copiés dans dist/."""
    build_dist.preparer_dossier_production()

    assert (site_minimal / "robots.txt").is_file()
    assert (site_minimal / "sitemap.xml").is_file()


def test_preparer_dossier_production_publie_service_worker(
    site_minimal: Path,
) -> None:
    """Le service worker (sw.js) est copié à la racine de dist/."""
    build_dist.preparer_dossier_production()

    assert (site_minimal / "sw.js").is_file()
