"""Modèles de validation des données documentaires (data/documents.json).

Ces modèles Pydantic constituent la frontière de validation entre la
configuration versionnée (``data/documents.json``) et le rendu des cartes.
Le contenu provient du dépôt (source maîtrisée), pas d'entrées utilisateur.
"""

from __future__ import annotations

import json
import re
import urllib.parse
from pathlib import Path
from typing import Annotated, Literal, Union

from pydantic import (
    AfterValidator,
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

# Schémas d'URL autorisés pour les liens et ressources des cartes. Les chemins
# relatifs (sans schéma) restent permis ; tout schéma exécutable
# (``javascript:``, ``data:``, ``vbscript:``, ``file:``...) est refusé pour
# empêcher une injection via data/documents.json, même si cette source venait
# un jour à être alimentée par une donnée moins maîtrisée.
SCHEMES_URL_AUTORISES = frozenset({"http", "https"})

# Caractères retirés par les navigateurs avant lecture du schéma d'une URL
# (tabulation, retours chariot/ligne) : on les neutralise pour éviter un
# contournement du type ``java\tscript:``.
_CARACTERES_URL_IGNORES = re.compile(r"[\t\r\n]")


def _valider_url_sure(valeur: str) -> str:
    """
    Valide une URL de carte contre les schémas dangereux.

    Autorise les chemins relatifs et les URL ``http``/``https`` absolues ;
    refuse les URL protocol-relative (``//hote``) et tout schéma exécutable.

    Args:
        valeur (str): URL ou chemin déclaré dans data/documents.json.

    Returns:
        str: La valeur d'origine si elle est jugée sûre.

    Raises:
        ValueError: Si l'URL est vide, protocol-relative ou à schéma interdit.
    """
    nettoyee = _CARACTERES_URL_IGNORES.sub("", valeur).strip()
    if not nettoyee:
        raise ValueError("URL vide")
    if nettoyee.startswith("//"):
        raise ValueError(f"URL protocol-relative interdite : {valeur!r}")
    schema = urllib.parse.urlparse(nettoyee).scheme.lower()
    if schema and schema not in SCHEMES_URL_AUTORISES:
        raise ValueError(f"Schéma d'URL interdit : {valeur!r}")
    return valeur


# URL sûre réutilisable : chemin relatif ou http(s), jamais de schéma exécutable.
UrlSure = Annotated[str, AfterValidator(_valider_url_sure)]

# Nom d'icône Lucide : minuscules, chiffres et tirets uniquement (anti-injection
# d'attribut dans ``data-lucide``, en complément de l'auto-échappement Jinja2).
NomIcone = Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]*$")]


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
    src: UrlSure
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

    # mypy ne gère pas les décorateurs empilés au-dessus de @property
    # (limitation « prop-decorator ») : on cible précisément ce code, le motif
    # @computed_field + @property étant l'idiome Pydantic recommandé.
    @computed_field  # type: ignore[prop-decorator]
    @property
    def srcset_avif(self) -> str:
        """srcset des variantes AVIF (vide si aucune largeur déclarée)."""
        return self._srcset("avif")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def srcset_webp(self) -> str:
        """srcset des variantes WebP (vide si aucune largeur déclarée)."""
        return self._srcset("webp")


class MediaQr(BaseModel):
    """Encart QR code menant à une ressource imprimable (ex. flyer)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["qr"]
    href: UrlSure
    qr_src: UrlSure
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
    icon: NomIcone
    badge_label: str
    badge_color: CouleurBadge
    version_label: str
    title: str
    description_html: str
    key_points: list[str] = Field(min_length=1)
    footer_note: str
    cta_label: str
    cta_href: UrlSure
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
