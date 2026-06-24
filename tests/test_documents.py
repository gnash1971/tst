"""Tests du pilotage par données des cartes documentaires.

Couvre la validation du schéma (models.py) et le rendu Jinja2 des cartes
(build_index.py), garantissant l'absence de régression après la suppression
des fragments partials/doc-card-*.html.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import build_index
import models

# ---------------------------------------------------------------------------
# Données de test
# ---------------------------------------------------------------------------


def _carte_valide() -> dict[str, Any]:
    """Retourne une carte minimale et conforme au schéma."""
    return {
        "id": "doc-test",
        "category": "club",
        "accent": "emerald",
        "icon_color": "blue",
        "icon": "file-text",
        "badge_label": "Test",
        "badge_color": "sky",
        "version_label": "V1",
        "title": "Titre de test",
        "description_html": "<strong>Description</strong> de test.",
        "key_points": ["Point A", "Point B"],
        "footer_note": "Note de pied",
        "cta_label": "Consulter",
        "cta_href": "fic/test.html",
        "search": "test recherche mots clés",
        "media": None,
    }


def _ecrire_et_charger(tmp_path: Path, donnees: object) -> list[models.DocumentCard]:
    """Écrit ``donnees`` en JSON puis tente de les charger/valider."""
    fichier = tmp_path / "documents.json"
    fichier.write_text(json.dumps(donnees, ensure_ascii=False), encoding="utf-8")
    return models.charger_documents(fichier)


# ---------------------------------------------------------------------------
# Validation du schéma (models.charger_documents)
# ---------------------------------------------------------------------------


def test_charger_documents_fichier_reel() -> None:
    """Le fichier data/documents.json réel contient 6 cartes valides."""
    documents = models.charger_documents(build_index.DATA_PATH)

    assert len(documents) == 6
    identifiants = {doc.id for doc in documents}
    assert identifiants == {
        "doc-fiche-inscription",
        "doc-reglement-interieur",
        "doc-pv-ag",
        "doc-statuts",
        "doc-maillot",
        "doc-flyer",
    }


def test_charger_documents_carte_minimale(tmp_path: Path) -> None:
    """Une carte conforme est chargée sans erreur."""
    documents = _ecrire_et_charger(tmp_path, [_carte_valide()])

    assert len(documents) == 1
    assert documents[0].id == "doc-test"


def test_charger_documents_media_image(tmp_path: Path) -> None:
    """Un média de type image est validé en MediaImage."""
    carte = _carte_valide()
    carte["media"] = {
        "type": "image",
        "src": "pub/x.png",
        "alt": "alt",
        "aria_label": "agrandir",
    }

    documents = _ecrire_et_charger(tmp_path, [carte])

    assert isinstance(documents[0].media, models.MediaImage)


def test_charger_documents_media_qr(tmp_path: Path) -> None:
    """Un média de type qr est validé en MediaQr."""
    carte = _carte_valide()
    carte["media"] = {
        "type": "qr",
        "href": "pub/flyer.html",
        "qr_src": "pub/qr.svg",
        "kicker": "k",
        "title": "t",
        "subtitle": "s",
        "aria_label": "a",
    }

    documents = _ecrire_et_charger(tmp_path, [carte])

    assert isinstance(documents[0].media, models.MediaQr)


def test_charger_documents_couleur_accent_invalide(tmp_path: Path) -> None:
    """Une couleur d'accent hors palette est rejetée."""
    carte = _carte_valide()
    carte["accent"] = "turquoise"

    with pytest.raises(models.DocumentsConfigError):
        _ecrire_et_charger(tmp_path, [carte])


def test_charger_documents_champ_manquant(tmp_path: Path) -> None:
    """L'absence d'un champ obligatoire est rejetée."""
    carte = _carte_valide()
    del carte["title"]

    with pytest.raises(models.DocumentsConfigError):
        _ecrire_et_charger(tmp_path, [carte])


def test_charger_documents_champ_supplementaire(tmp_path: Path) -> None:
    """Un champ inconnu est rejeté (extra='forbid' : détecte les fautes)."""
    carte = _carte_valide()
    carte["couleur"] = "rouge"

    with pytest.raises(models.DocumentsConfigError):
        _ecrire_et_charger(tmp_path, [carte])


def test_charger_documents_media_discriminant_invalide(tmp_path: Path) -> None:
    """Un type de média inconnu est rejeté par l'union discriminée."""
    carte = _carte_valide()
    carte["media"] = {"type": "video", "src": "x.mp4"}

    with pytest.raises(models.DocumentsConfigError):
        _ecrire_et_charger(tmp_path, [carte])


def test_charger_documents_key_points_vide(tmp_path: Path) -> None:
    """Une liste de points clés vide est rejetée (min_length=1)."""
    carte = _carte_valide()
    carte["key_points"] = []

    with pytest.raises(models.DocumentsConfigError):
        _ecrire_et_charger(tmp_path, [carte])


def test_charger_documents_json_invalide(tmp_path: Path) -> None:
    """Un JSON mal formé lève une erreur de configuration explicite."""
    fichier = tmp_path / "documents.json"
    fichier.write_text("ceci n'est pas du json {", encoding="utf-8")

    with pytest.raises(models.DocumentsConfigError):
        models.charger_documents(fichier)


def test_charger_documents_pas_une_liste(tmp_path: Path) -> None:
    """Un document racine non-liste est rejeté."""
    with pytest.raises(models.DocumentsConfigError):
        _ecrire_et_charger(tmp_path, {"id": "x"})


def test_charger_documents_fichier_absent(tmp_path: Path) -> None:
    """Un fichier absent lève une erreur de configuration explicite."""
    with pytest.raises(models.DocumentsConfigError):
        models.charger_documents(tmp_path / "absent.json")


# ---------------------------------------------------------------------------
# Rendu des cartes (build_index.rendre_cartes_documents) — données réelles
# ---------------------------------------------------------------------------


def test_rendre_cartes_contient_chaque_document() -> None:
    """Chaque carte réelle est présente avec ses attributs essentiels."""
    html = build_index.rendre_cartes_documents()
    documents = models.charger_documents(build_index.DATA_PATH)

    for doc in documents:
        assert f'id="{doc.id}"' in html
        assert f'data-category="{doc.category}"' in html
        assert f'data-search="{doc.search}"' in html
        assert doc.cta_href in html
        assert doc.cta_label in html


def test_rendre_cartes_nombre_de_cartes() -> None:
    """Le nombre de cartes rendues correspond au nombre de documents."""
    html = build_index.rendre_cartes_documents()
    documents = models.charger_documents(build_index.DATA_PATH)

    assert html.count('class="doc-card') == len(documents)


def test_rendre_cartes_sans_syntaxe_jinja() -> None:
    """Aucune syntaxe de gabarit ne subsiste dans le rendu."""
    html = build_index.rendre_cartes_documents()

    assert "{{" not in html
    assert "{%" not in html


def test_rendre_cartes_medias_image_et_qr() -> None:
    """Les blocs média (image du maillot, QR du flyer) sont rendus."""
    html = build_index.rendre_cartes_documents()

    assert 'src="pub/V5_t-shirts.png"' in html
    assert 'src="pub/qr_l-tt-club.svg"' in html
    assert 'loading="lazy"' in html


def test_rendre_cartes_couleurs_par_accent() -> None:
    """Les classes Tailwind dépendent bien de l'accent de chaque carte."""
    html = build_index.rendre_cartes_documents()

    # Maillot : accent sky ; PV/Statuts : accent orange.
    assert "bg-sky-600 dark:bg-sky-500" in html
    assert "bg-orange-600 dark:bg-orange-500" in html
    assert "hover:border-emerald-500/40" in html


# ---------------------------------------------------------------------------
# Injection dans le modèle (build_index.injecter_documents)
# ---------------------------------------------------------------------------


def test_injecter_documents_remplace_directive() -> None:
    """La directive @documents est remplacée par les cartes rendues."""
    contenu = "<section>\n<!-- @documents -->\n</section>"

    resultat = build_index.injecter_documents(contenu)

    assert "<!-- @documents -->" not in resultat
    assert 'id="doc-fiche-inscription"' in resultat
    assert 'class="doc-card' in resultat


def test_injecter_documents_sans_directive() -> None:
    """Un contenu sans directive @documents ressort inchangé."""
    contenu = "<section><p>Rien à injecter</p></section>"

    assert build_index.injecter_documents(contenu) == contenu
