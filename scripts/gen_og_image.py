"""Génère l'image de partage Open Graph (1200x630) du portail LTT.

Outil de développement : compose un visuel de marque (dégradé vert vers navy,
carte blanche contenant le logo du club, accroche et URL) dans
``pub/og-image.png``. Les polices Exo 2 / Inter sont récupérées en TTF auprès
de l'API gwfh (même hôte autorisé que ``scripts/download_fonts.py``) et mises
en cache localement, avec repli sur une police système puis sur la police par
défaut de Pillow si le réseau est indisponible.

Usage :
    python scripts/gen_og_image.py
"""

from __future__ import annotations

import json
import logging
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import cast

from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Resampling

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("gen_og_image")

ROOT_DIR = Path(__file__).resolve().parent.parent
PUB_DIR = ROOT_DIR / "pub"
LOGO_SRC = ROOT_DIR / "logo" / "V5_logo_fonds_clairs.png"
CACHE_DIR = Path(__file__).resolve().parent / "_assets_cache"

LARGEUR = 1200
HAUTEUR = 630
SORTIE = PUB_DIR / "og-image.png"

# Contenu éditorial de la carte de partage.
ACCROCHE = "Préparez votre saison au ping"
SOUS_TITRE = "Tous les documents officiels du club"
BADGE = "ESPACE DOCUMENTAIRE OFFICIEL"
URL_SITE = "www.l-tt.club"

# Couleurs de marque (cohérentes avec css/base.css et tailwind.config.js).
VERT = (21, 128, 61)
NAVY = (2, 6, 23)
ORANGE = (249, 115, 22)
BLANC = (255, 255, 255)
VERT_CLAIR = (134, 239, 172)
GRIS_CLAIR = (203, 213, 225)

# Récupération des polices (mêmes garde-fous que download_fonts.py).
API_URL_TEMPLATE = "https://gwfh.mranftl.com/api/fonts/{font_id}?subsets=latin"
HOTES_AUTORISES = frozenset({"gwfh.mranftl.com", "fonts.gstatic.com"})
TIMEOUT_S = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
# Taille maximale d'un téléchargement (anti-saturation mémoire/disque).
TAILLE_MAX_TELECHARGEMENT = 5 * 1024 * 1024
# Format strict des identifiants de police (anti-injection URL/chemin).
MOTIF_IDENTIFIANT = re.compile(r"^[a-z0-9-]+$")

# Polices système de repli (Windows en priorité, puis Linux).
REPLIS_GRAS = (
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)
REPLIS_NORMAL = (
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def _valider_url(url: str) -> None:
    """Vérifie qu'une URL de police est HTTPS vers un hôte autorisé.

    Args:
        url: URL renvoyée par l'API de polices.

    Raises:
        ValueError: Si le schéma ou l'hôte n'est pas autorisé.
    """
    analyse = urllib.parse.urlparse(url)
    if analyse.scheme != "https" or analyse.hostname not in HOTES_AUTORISES:
        raise ValueError(f"URL de police refusée : {url}")


class _RedirectionValidee(urllib.request.HTTPRedirectHandler):
    """Revalide l'hôte cible à chaque redirection HTTP (défense anti-SSRF)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        # Refuse toute redirection vers un hôte hors de la liste blanche.
        _valider_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


# Ouvreur dédié : applique la revalidation d'hôte sur les redirections.
_OUVREUR = urllib.request.build_opener(_RedirectionValidee())


def _valider_identifiant(valeur: str) -> None:
    """Vérifie le format d'un identifiant de police (anti-injection).

    Args:
        valeur: Identifiant de police ou de variante.

    Raises:
        ValueError: Si l'identifiant contient des caractères inattendus.
    """
    if not MOTIF_IDENTIFIANT.fullmatch(valeur):
        raise ValueError(f"Identifiant de police refusé : {valeur!r}")


def _lire_limite(flux: object, taille_max: int) -> bytes:
    """Lit un flux en refusant les contenus dépassant la taille maximale.

    Args:
        flux: Flux ouvert exposant ``read(taille)``.
        taille_max: Nombre d'octets maximal autorisé.

    Returns:
        bytes: Contenu lu (au plus ``taille_max`` octets).

    Raises:
        ValueError: Si le contenu distant dépasse ``taille_max``.
    """
    donnees = cast(bytes, flux.read(taille_max + 1))  # type: ignore[attr-defined]
    if len(donnees) > taille_max:
        raise ValueError("Contenu distant trop volumineux : abandon du téléchargement.")
    return donnees


def telecharger_ttf(font_id: str, variant_id: str) -> Path | None:
    """Récupère une variante TTF depuis l'API gwfh et la met en cache.

    La récupération est durcie : identifiants validés, hôte vérifié à chaque
    redirection et taille de téléchargement bornée.

    Args:
        font_id: Identifiant de la police (ex : ``exo-2``).
        variant_id: Identifiant de variante (ex : ``800``).

    Returns:
        Path | None: Chemin du TTF local, ou ``None`` si indisponible.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = CACHE_DIR / f"{font_id}-{variant_id}.ttf"
    if cache.is_file():
        return cache

    try:
        _valider_identifiant(font_id)
        _valider_identifiant(variant_id)
        url_api = API_URL_TEMPLATE.format(font_id=font_id)
        _valider_url(url_api)
        requete = urllib.request.Request(url_api, headers={"User-Agent": USER_AGENT})
        with _OUVREUR.open(requete, timeout=TIMEOUT_S) as reponse:
            _valider_url(reponse.geturl())
            charge = _lire_limite(reponse, TAILLE_MAX_TELECHARGEMENT)
            meta = json.loads(charge.decode("utf-8"))

        for variante in meta.get("variants", []):
            if variante.get("id") != variant_id:
                continue
            url_ttf = variante.get("ttf")
            if not url_ttf:
                return None
            _valider_url(url_ttf)
            requete_ttf = urllib.request.Request(
                url_ttf, headers={"User-Agent": USER_AGENT}
            )
            with _OUVREUR.open(requete_ttf, timeout=TIMEOUT_S) as flux:
                _valider_url(flux.geturl())
                cache.write_bytes(_lire_limite(flux, TAILLE_MAX_TELECHARGEMENT))
            return cache
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError,
            ValueError, OSError) as erreur:
        logger.warning(f"Police {font_id} {variant_id} indisponible : {erreur}")
        return None
    return None


def charger_police(
    font_id: str, variant_id: str, taille: int, replis: tuple[str, ...]
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Charge une police TTF avec repli système puis police par défaut.

    Args:
        font_id: Identifiant gwfh de la police de marque.
        variant_id: Identifiant de variante gwfh.
        taille: Taille de la police en points.
        replis: Chemins de polices système de repli.

    Returns:
        Police chargée, prête pour le dessin.
    """
    chemin = telecharger_ttf(font_id, variant_id)
    if chemin is not None:
        try:
            return ImageFont.truetype(str(chemin), taille)
        except OSError as erreur:
            logger.warning(f"Chargement TTF échoué ({chemin}) : {erreur}")

    for repli in replis:
        try:
            return ImageFont.truetype(repli, taille)
        except OSError:
            continue

    logger.warning("Repli sur la police bitmap par défaut de Pillow.")
    return ImageFont.load_default(size=taille)


def degrade_diagonal(
    couleur_haut: tuple[int, int, int], couleur_bas: tuple[int, int, int]
) -> Image.Image:
    """Construit un dégradé vertical entre deux couleurs.

    Args:
        couleur_haut: Couleur RVB du haut.
        couleur_bas: Couleur RVB du bas.

    Returns:
        Image.Image: Fond RGB dégradé aux dimensions de la carte.
    """
    base = Image.new("RGB", (LARGEUR, HAUTEUR), couleur_haut)
    dessin = ImageDraw.Draw(base)
    for y in range(HAUTEUR):
        ratio = y / (HAUTEUR - 1)
        couleur = tuple(
            int(couleur_haut[i] + (couleur_bas[i] - couleur_haut[i]) * ratio)
            for i in range(3)
        )
        dessin.line([(0, y), (LARGEUR, y)], fill=couleur)
    return base


def ajouter_lueur(
    fond: Image.Image, centre: tuple[int, int], rayon: int,
    couleur: tuple[int, int, int], opacite: int
) -> None:
    """Superpose une lueur radiale douce (rappel du fond du site).

    Args:
        fond: Image de fond RGB modifiée sur place.
        centre: Centre (x, y) de la lueur.
        rayon: Rayon de la lueur en pixels.
        couleur: Couleur RVB de la lueur.
        opacite: Opacité maximale au centre (0-255).
    """
    calque = Image.new("RGBA", fond.size, (0, 0, 0, 0))
    dessin = ImageDraw.Draw(calque)
    pas = 24
    for etape in range(pas, 0, -1):
        r = int(rayon * etape / pas)
        alpha = int(opacite * (1 - etape / pas))
        dessin.ellipse(
            [centre[0] - r, centre[1] - r, centre[0] + r, centre[1] + r],
            fill=couleur + (alpha,),
        )
    fond.paste(calque, (0, 0), calque)


def envelopper_texte(
    dessin: ImageDraw.ImageDraw, texte: str,
    police: ImageFont.FreeTypeFont | ImageFont.ImageFont, largeur_max: int
) -> list[str]:
    """Découpe un texte en lignes tenant dans une largeur donnée.

    Args:
        dessin: Contexte de dessin pour mesurer le texte.
        texte: Texte à envelopper.
        police: Police utilisée pour la mesure.
        largeur_max: Largeur maximale d'une ligne en pixels.

    Returns:
        list[str]: Lignes résultantes.
    """
    mots = texte.split()
    lignes: list[str] = []
    courante = ""
    for mot in mots:
        essai = f"{courante} {mot}".strip()
        if dessin.textlength(essai, font=police) <= largeur_max:
            courante = essai
        else:
            if courante:
                lignes.append(courante)
            courante = mot
    if courante:
        lignes.append(courante)
    return lignes


def composer_image() -> Image.Image:
    """Compose la carte de partage Open Graph complète.

    Returns:
        Image.Image: Image RGB 1200x630 prête à enregistrer.

    Raises:
        FileNotFoundError: Si le logo source est introuvable.
    """
    if not LOGO_SRC.is_file():
        raise FileNotFoundError(f"Logo source introuvable : {LOGO_SRC}")

    fond = degrade_diagonal(VERT, NAVY)
    ajouter_lueur(fond, (150, 90), 380, VERT_CLAIR, 60)
    ajouter_lueur(fond, (1080, 70), 320, ORANGE, 45)

    carte = fond.convert("RGBA")
    dessin = ImageDraw.Draw(carte)

    # Carte blanche arrondie contenant le logo (le fond blanc du logo se fond).
    carte_boite = (72, 150, 532, 480)
    dessin.rounded_rectangle(carte_boite, radius=28, fill=BLANC + (255,))

    with Image.open(LOGO_SRC) as source:
        logo = source.convert("RGBA")
    marge_carte = 44
    largeur_dispo = (carte_boite[2] - carte_boite[0]) - 2 * marge_carte
    hauteur_dispo = (carte_boite[3] - carte_boite[1]) - 2 * marge_carte
    ratio = min(largeur_dispo / logo.width, hauteur_dispo / logo.height)
    logo_redim = logo.resize(
        (int(logo.width * ratio), int(logo.height * ratio)), Resampling.LANCZOS
    )
    pos_logo = (
        carte_boite[0] + (carte_boite[2] - carte_boite[0] - logo_redim.width) // 2,
        carte_boite[1] + (carte_boite[3] - carte_boite[1] - logo_redim.height) // 2,
    )
    carte.alpha_composite(logo_redim, pos_logo)

    # Colonne de texte à droite.
    police_badge = charger_police("exo-2", "600", 26, REPLIS_GRAS)
    police_titre = charger_police("exo-2", "800", 62, REPLIS_GRAS)
    police_sous = charger_police("inter", "regular", 30, REPLIS_NORMAL)
    police_url = charger_police("exo-2", "700", 34, REPLIS_GRAS)

    x_texte = 600
    largeur_texte = LARGEUR - x_texte - 72

    # Pastille « badge » avec contour translucide.
    badge_largeur = dessin.textlength(BADGE, font=police_badge) + 48
    dessin.rounded_rectangle(
        [x_texte, 150, x_texte + badge_largeur, 198],
        radius=24, fill=(255, 255, 255, 28), outline=(255, 255, 255, 90), width=2,
    )
    dessin.text(
        (x_texte + 24, 174), BADGE, font=police_badge, fill=VERT_CLAIR, anchor="lm"
    )

    # Accroche principale (titre), enveloppée si nécessaire.
    y = 236
    for ligne in envelopper_texte(dessin, ACCROCHE, police_titre, largeur_texte):
        dessin.text((x_texte, y), ligne, font=police_titre, fill=BLANC)
        y += 74

    # Sous-titre éditorial.
    y += 6
    dessin.text((x_texte, y), SOUS_TITRE, font=police_sous, fill=GRIS_CLAIR)

    # Ligne URL avec une balle orange (rappel sportif).
    y_url = 470
    rayon_balle = 13
    dessin.ellipse(
        [x_texte, y_url - rayon_balle, x_texte + 2 * rayon_balle, y_url + rayon_balle],
        fill=ORANGE,
    )
    dessin.text(
        (x_texte + 2 * rayon_balle + 16, y_url), URL_SITE,
        font=police_url, fill=BLANC, anchor="lm",
    )

    return carte.convert("RGB")


def main() -> int:
    """Génère et enregistre l'image Open Graph du site.

    Returns:
        int: 0 en cas de succès, 1 en cas d'erreur.
    """
    try:
        image = composer_image()
    except FileNotFoundError as erreur:
        logger.error(str(erreur))
        return 1

    PUB_DIR.mkdir(parents=True, exist_ok=True)
    image.save(SORTIE, "PNG", optimize=True)
    logger.info(f"Image Open Graph générée : {SORTIE} ({LARGEUR}x{HAUTEUR})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
