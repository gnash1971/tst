"""Génère les variantes WebP/AVIF des images matricielles du site.

Outil de développement : les variantes sont produites localement puis
versionnées (build_dist.py copie logo/ et pub/ tels quels). Netlify n'a donc
pas besoin de Pillow au moment du build.

Utilisation :
    python scripts/generate_images.py          # ne régénère que si nécessaire
    python scripts/generate_images.py --force   # régénère tout
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent.parent

# Qualité des encodeurs (suffisante pour des logos et visuels web).
WEBP_QUALITY = 80
AVIF_QUALITY = 62
FORMATS = ("avif", "webp")


@dataclass(frozen=True)
class SpecImage:
    """Source matricielle et largeurs cibles (en pixels) à générer."""

    source: str
    widths: tuple[int, ...]


# Largeurs adaptées aux usages : 96 (footer 32px, header 48px @1-2x),
# 256 (header retina, carte visuelle), 768 (filigrane du hero, en basse
# opacité). Maillot : 400/800 (carte large, gros gain face au PNG d'1 Mo).
IMAGES: tuple[SpecImage, ...] = (
    SpecImage("logo/V5_logo_fonds_clairs.png", (96, 256, 768)),
    SpecImage("logo/V5_logo_fonds_sombres.png", (96, 256, 768)),
    SpecImage("pub/V5_t-shirts.png", (400, 800)),
)


def _redimensionner(image: Image.Image, largeur_cible: int) -> Image.Image:
    """Redimensionne en conservant le ratio, sans jamais agrandir."""
    largeur, hauteur = image.size
    if largeur_cible >= largeur:
        return image
    hauteur_cible = max(1, round(hauteur * largeur_cible / largeur))
    return image.resize((largeur_cible, hauteur_cible), Image.Resampling.LANCZOS)


def _enregistrer(image: Image.Image, destination: Path, fmt: str) -> None:
    """Encode l'image au format demandé (webp ou avif)."""
    if fmt == "webp":
        image.save(destination, format="WEBP", quality=WEBP_QUALITY, method=6)
    elif fmt == "avif":
        image.save(destination, format="AVIF", quality=AVIF_QUALITY)
    else:
        raise ValueError(f"Format non supporté : {fmt}")


def generer(force: bool = False) -> list[Path]:
    """
    Génère toutes les variantes déclarées dans IMAGES.

    Args:
        force: Régénère même si la variante est plus récente que la source.

    Returns:
        list[Path]: Variantes effectivement (re)générées.
    """
    generes: list[Path] = []

    for spec in IMAGES:
        source = ROOT_DIR / spec.source
        if not source.is_file():
            print(f"Avertissement : source introuvable ({source}).", file=sys.stderr)
            continue

        mtime_source = source.stat().st_mtime
        with Image.open(source) as image:
            image.load()
            base = image if image.mode in ("RGB", "RGBA") else image.convert("RGBA")

            for largeur in spec.widths:
                if largeur >= base.size[0]:
                    # Pas d'agrandissement : la largeur cible dépasse la source.
                    continue
                vignette = _redimensionner(base, largeur)
                for fmt in FORMATS:
                    destination = source.with_name(f"{source.stem}-{largeur}.{fmt}")
                    if (
                        not force
                        and destination.is_file()
                        and destination.stat().st_mtime >= mtime_source
                    ):
                        continue
                    _enregistrer(vignette, destination, fmt)
                    generes.append(destination)
                    print(f"Généré : {destination.relative_to(ROOT_DIR)}")

    return generes


if __name__ == "__main__":
    variantes = generer(force="--force" in sys.argv)
    print(f"{len(variantes)} variante(s) générée(s).")
