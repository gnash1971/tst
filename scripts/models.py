"""Modèles de validation des données documentaires (data/documents.json).

Ces modèles Pydantic constituent la frontière de validation entre la
configuration versionnée (``data/documents.json``) et le rendu des cartes.
Le contenu provient du dépôt (source maîtrisée), pas d'entrées utilisateur.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    computed_field,
)

# Palettes Tailwind autorisées (cohérentes avec js/tailwind.config.js).
# ``accent`` pilote la structure (barre, survol, puces, titre, bouton) ;
# ``icon_color`` la pastille d'identité ; ``badge_color`` l'étiquette.
CouleurAccent = Literal["emerald", "orange", "sky"]
CouleurIcone = Literal["purple", "blue", "green", "red", "sky", "emerald", "orange"]
CouleurBadge = Literal["emerald", "orange", "sky"]
Categorie = Literal["administratif", "juridique", "club"]


class DocumentsConfigError(Exception):
    """Erreur de chargement ou de validation de data/documents.json."""


class MediaImage(BaseModel):
    """Visuel illustratif d'une carte (ex. maillot du club).

    Si ``widths`` est renseigné, le rendu produit un ``<picture>`` avec des
    sources AVIF/WebP réactives (variantes nommées ``<stem>-<largeur>.<fmt>``
    générées par scripts/generate_images.py). Sinon, un simple ``<img>``.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["image"]
    src: str
    alt: str
    aria_label: str
    widths: list[int] = Field(default_factory=list)
    sizes: str | None = None

    def _srcset(self, fmt: str) -> str:
        """Construit l'attribut ``srcset`` pour un format donné."""
        if not self.widths:
            return ""
        stem = self.src.rsplit(".", 1)[0]
        return ", ".join(f"{stem}-{largeur}.{fmt} {largeur}w" for largeur in self.widths)

    @computed_field
    @property
    def srcset_avif(self) -> str:
        """srcset des variantes AVIF (vide si aucune largeur déclarée)."""
        return self._srcset("avif")

    @computed_field
    @property
    def srcset_webp(self) -> str:
        """srcset des variantes WebP (vide si aucune largeur déclarée)."""
        return self._srcset("webp")


class MediaQr(BaseModel):
    """Encart QR code menant à une ressource imprimable (ex. flyer)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["qr"]
    href: str
    qr_src: str
    kicker: str
    title: str
    subtitle: str
    aria_label: str


# Union discriminée sur le champ ``type`` : sélectionne le bon média.
Media = Annotated[Union[MediaImage, MediaQr], Field(discriminator="type")]


class DocumentCard(BaseModel):
    """Carte documentaire affichée dans la grille de la page d'accueil."""

    model_config = ConfigDict(extra="forbid")

    id: str
    category: Categorie
    accent: CouleurAccent
    icon_color: CouleurIcone
    icon: str
    badge_label: str
    badge_color: CouleurBadge
    version_label: str
    title: str
    description_html: str
    key_points: list[str] = Field(min_length=1)
    footer_note: str
    cta_label: str
    cta_href: str
    search: str
    media: Media | None = None


def charger_documents(chemin: Path) -> list[DocumentCard]:
    """
    Charge et valide la liste des cartes documentaires.

    Args:
        chemin: Chemin vers le fichier data/documents.json.

    Returns:
        list[DocumentCard]: Cartes validées, dans l'ordre du fichier.

    Raises:
        DocumentsConfigError: Si le fichier est absent, illisible, mal formé
            (JSON) ou non conforme au schéma (validation Pydantic).
    """
    if not chemin.is_file():
        raise DocumentsConfigError(f"Fichier de documents introuvable : {chemin}")

    try:
        donnees = json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DocumentsConfigError(
            f"JSON invalide dans {chemin} : {exc}"
        ) from exc

    if not isinstance(donnees, list):
        raise DocumentsConfigError(
            f"Le fichier {chemin} doit contenir une liste de documents."
        )

    try:
        return [DocumentCard.model_validate(item) for item in donnees]
    except ValidationError as exc:
        raise DocumentsConfigError(
            f"Document non conforme au schéma dans {chemin} :\n{exc}"
        ) from exc
