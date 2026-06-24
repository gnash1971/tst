"""Tests de la factorisation du thème Tailwind.

Garantit que js/tailwind.config.js (Play CDN) est généré depuis la source
unique data/brand-theme.json et reste synchronisé avec elle.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import build_index


def test_generer_config_ecrit_le_theme(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """La config CDN générée reprend le thème fourni et la syntaxe attendue."""
    theme = {"colors": {"brand": {"court": "#123456"}}, "fontFamily": {}}
    source = tmp_path / "brand-theme.json"
    source.write_text(json.dumps(theme), encoding="utf-8")
    sortie = tmp_path / "tailwind.config.js"
    monkeypatch.setattr(build_index, "BRAND_THEME_PATH", source)
    monkeypatch.setattr(build_index, "JS_TAILWIND_CONFIG_PATH", sortie)

    build_index.generer_config_tailwind_cdn()

    contenu = sortie.read_text(encoding="utf-8")
    assert contenu.startswith("/*")
    assert "tailwind.config = {" in contenu
    assert '"darkMode": "class"' in contenu
    assert "#123456" in contenu


def test_generer_config_theme_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sans fichier de thème, aucune config n'est écrite (avertissement)."""
    sortie = tmp_path / "tailwind.config.js"
    monkeypatch.setattr(build_index, "BRAND_THEME_PATH", tmp_path / "absent.json")
    monkeypatch.setattr(build_index, "JS_TAILWIND_CONFIG_PATH", sortie)

    build_index.generer_config_tailwind_cdn()

    assert not sortie.exists()


def test_config_cdn_synchronisee_avec_theme(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Le js/tailwind.config.js commité est à jour vis-à-vis du thème source."""
    attendu = build_index.JS_TAILWIND_CONFIG_PATH.read_text(encoding="utf-8")
    sortie = tmp_path / "tailwind.config.js"
    monkeypatch.setattr(build_index, "JS_TAILWIND_CONFIG_PATH", sortie)

    build_index.generer_config_tailwind_cdn()

    assert sortie.read_text(encoding="utf-8") == attendu


def test_config_cdn_contenu_json_valide() -> None:
    """Le corps de la config CDN est un objet JSON cohérent avec le thème."""
    contenu = build_index.JS_TAILWIND_CONFIG_PATH.read_text(encoding="utf-8")
    objet = json.loads(contenu[contenu.index("{") : contenu.rindex("}") + 1])
    theme = json.loads(build_index.BRAND_THEME_PATH.read_text(encoding="utf-8"))

    assert objet["darkMode"] == "class"
    assert objet["theme"]["extend"] == theme
