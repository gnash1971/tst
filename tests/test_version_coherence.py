"""Test de cohérence de version entre package.json et pyproject.toml.

Les deux fichiers déclarent la version du projet ; ce test empêche qu'elles
divergent silencieusement.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_JSON = ROOT / "package.json"
PYPROJECT = ROOT / "pyproject.toml"


def _version_package_json() -> str:
    """Lit la version déclarée dans package.json."""
    data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    return str(data["version"])


def _version_pyproject() -> str:
    """Lit la version déclarée dans pyproject.toml."""
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def test_versions_synchronisees() -> None:
    """package.json et pyproject.toml déclarent la même version."""
    assert _version_package_json() == _version_pyproject()
