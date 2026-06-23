"""Génère les favicons et icônes PWA du portail LTT depuis le logo du club.

Outil de développement : isole l'écusson du logo
(``logo/V5_logo_fonds_clairs.png``) pour produire un favicon lisible même en
16x16, puis exporte ``favicon.ico`` à la racine et les icônes
apple-touch / PWA dans ``logo/``.

Usage :
    python scripts/gen_favicons.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PIL import Image, ImageChops
from PIL.Image import Resampling

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("gen_favicons")

ROOT_DIR = Path(__file__).resolve().parent.parent
LOGO_SRC = ROOT_DIR / "logo" / "V5_logo_fonds_clairs.png"
LOGO_DIR = ROOT_DIR / "logo"

BLANC = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)

# Tailles incluses dans le favicon.ico multi-résolutions.
TAILLES_ICO = [(16, 16), (32, 32), (48, 48), (64, 64)]
# Seuil de dominance du bleu (b - max(r, g)) pour le blason.
SEUIL_BLEU = 25
# Seuils de détection du doré (raquette / balle) : r-b élevé, bleu faible.
SEUIL_OR_RB = 35
SEUIL_OR_ROUGE = 110
SEUIL_OR_BLEU = 130
# Seuil de luminosité au-delà duquel un pixel est considéré « fond blanc ».
SEUIL_BLANC = 238
# Marge autour de l'emblème (proportion du plus grand côté).
MARGE_EMBLEME = 0.07


class GenerationIconeError(Exception):
    """Erreur métier lors de la génération des icônes."""


def isoler_embleme() -> Image.Image:
    """Recadre le logo sur l'emblème (blason + raquette) dans un carré transparent.

    L'emblème est la partie reconnaissable du logo. Il est délimité par l'union
    des pixels à dominante bleue (blason) et dorée (raquette, balle), ce qui
    exclut nativement le bandeau de texte noir, illisible aux petites tailles.
    Le fond blanc résiduel est rendu transparent pour s'adapter aux thèmes
    clairs comme sombres des navigateurs.

    Returns:
        Image.Image: Emblème RGBA centré sur un canevas carré transparent.

    Raises:
        GenerationIconeError: Si le logo source ou l'emblème est introuvable.
    """
    if not LOGO_SRC.is_file():
        raise GenerationIconeError(f"Logo source introuvable : {LOGO_SRC}")

    with Image.open(LOGO_SRC) as source:
        logo = source.convert("RGBA")

    rouge, vert, bleu, _ = logo.split()
    # Masque du blason : dominance du bleu = bleu - max(rouge, vert).
    masque_bleu = ImageChops.subtract(bleu, ImageChops.lighter(rouge, vert)).point(
        lambda v: 255 if v > SEUIL_BLEU else 0
    )
    # Masque du doré : rouge nettement supérieur au bleu (ImageChops.multiply
    # agit comme un ET logique sur des masques binaires 0/255).
    masque_or = ImageChops.multiply(
        ImageChops.multiply(
            ImageChops.subtract(rouge, bleu).point(
                lambda v: 255 if v > SEUIL_OR_RB else 0
            ),
            rouge.point(lambda v: 255 if v > SEUIL_OR_ROUGE else 0),
        ),
        bleu.point(lambda v: 255 if v < SEUIL_OR_BLEU else 0),
    )
    boite = ImageChops.lighter(masque_bleu, masque_or).getbbox()
    if boite is None:
        raise GenerationIconeError("Emblème introuvable dans le logo.")

    # Marge légère pour aérer l'emblème (texte déjà exclu par les masques).
    gauche, haut, droite, bas = boite
    marge = int(max(droite - gauche, bas - haut) * MARGE_EMBLEME)
    gauche = max(0, gauche - marge)
    haut = max(0, haut - marge)
    droite = min(logo.width, droite + marge)
    bas = min(logo.height, bas + marge)

    embleme = logo.crop((gauche, haut, droite, bas))

    # Rend transparent le fond blanc tout en conservant les contours colorés.
    er, eg, eb, _ = embleme.split()
    min_canal = ImageChops.darker(ImageChops.darker(er, eg), eb)
    alpha = min_canal.point(lambda v: 0 if v > SEUIL_BLANC else 255)
    embleme.putalpha(alpha)

    cote = max(embleme.width, embleme.height)
    canevas = Image.new("RGBA", (cote, cote), TRANSPARENT)
    decalage = ((cote - embleme.width) // 2, (cote - embleme.height) // 2)
    canevas.alpha_composite(embleme, decalage)
    return canevas


def exporter_png(
    base: Image.Image,
    taille: int,
    destination: Path,
    fond: tuple[int, int, int, int] | None = None,
) -> None:
    """Redimensionne l'écusson et enregistre une icône PNG.

    Args:
        base: Écusson carré RGBA source.
        taille: Côté de l'icône cible en pixels.
        destination: Chemin du fichier PNG à écrire.
        fond: Couleur RGBA opaque à appliquer derrière (None = transparence).
    """
    image = base.resize((taille, taille), Resampling.LANCZOS)
    if fond is not None:
        plat = Image.new("RGBA", image.size, fond)
        plat.alpha_composite(image)
        image = plat
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)
    logger.info(f"Icône générée : {destination.name} ({taille}x{taille})")


def exporter_maskable(base: Image.Image, taille: int, destination: Path) -> None:
    """Enregistre une icône « maskable » avec zone de sécurité et fond plein.

    Les icônes maskables sont rognées par le système (cercle, goutte…) :
    l'écusson est donc réduit à ~70 % et posé sur un fond blanc plein.

    Args:
        base: Écusson carré RGBA source.
        taille: Côté de l'icône cible en pixels.
        destination: Chemin du fichier PNG à écrire.
    """
    fond = Image.new("RGBA", (taille, taille), BLANC)
    cote_interieur = int(taille * 0.70)
    contenu = base.resize((cote_interieur, cote_interieur), Resampling.LANCZOS)
    position = ((taille - cote_interieur) // 2, (taille - cote_interieur) // 2)
    fond.alpha_composite(contenu, position)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fond.save(destination)
    logger.info(f"Icône maskable générée : {destination.name} ({taille}x{taille})")


def main() -> int:
    """Génère l'ensemble des favicons et icônes du site.

    Returns:
        int: 0 en cas de succès, 1 en cas d'erreur métier.
    """
    try:
        embleme = isoler_embleme()
    except GenerationIconeError as erreur:
        logger.error(str(erreur))
        return 1

    favicon = ROOT_DIR / "favicon.ico"
    embleme.resize((256, 256), Resampling.LANCZOS).save(
        favicon, format="ICO", sizes=TAILLES_ICO
    )
    logger.info(f"favicon.ico généré : {favicon}")

    # Icônes PWA standard : transparence conservée.
    exporter_png(embleme, 192, LOGO_DIR / "icon-192.png")
    exporter_png(embleme, 512, LOGO_DIR / "icon-512.png")
    # apple-touch-icon : fond opaque exigé par iOS.
    exporter_png(embleme, 180, LOGO_DIR / "apple-touch-icon.png", fond=BLANC)
    # Icône maskable : marge de sécurité + fond plein.
    exporter_maskable(embleme, 512, LOGO_DIR / "maskable-512.png")

    logger.info("Toutes les icônes ont été générées avec succès.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
