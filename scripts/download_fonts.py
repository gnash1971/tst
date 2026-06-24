"""Télécharge les polices web (woff2) et régénère css/fonts.css.

Outil de développement uniquement (jamais exécuté en production) : interroge
l'API google-webfonts-helper (https://gwfh.mranftl.com) puis télécharge les
fichiers woff2 en local, pour un hébergement sans CDN compatible avec la CSP
stricte du site et le RGPD.
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
from typing import Any, cast

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("download_fonts")

# Chemins absolus du projet
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = PROJECT_ROOT / "fonts"
CSS_DIR = PROJECT_ROOT / "css"
FONTS_CSS_PATH = CSS_DIR / "fonts.css"

# Garde-fous réseau : seuls ces hôtes HTTPS sont autorisés au téléchargement.
API_URL_TEMPLATE = "https://gwfh.mranftl.com/api/fonts/{font_id}?subsets=latin"
HOTES_TELECHARGEMENT_AUTORISES = frozenset(
    {"gwfh.mranftl.com", "fonts.gstatic.com"}
)
TIMEOUT_S = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
# Taille maximale d'un téléchargement (anti-saturation mémoire/disque).
TAILLE_MAX_TELECHARGEMENT = 5 * 1024 * 1024

# Identifiants de variantes attendus (ex : regular, 600, 600italic).
MOTIF_VARIANTE = re.compile(r"^[a-z0-9]+$")

# Configuration des polices à télécharger
FONTS_CONFIG: dict[str, dict[str, Any]] = {
    "exo-2": {
        "variants": ["600", "700", "800", "600italic"],
        "family_name": "Exo 2",
    },
    "inter": {
        "variants": ["regular", "500", "600", "700", "800"],
        "family_name": "Inter",
    },
}


class TelechargementPoliceError(Exception):
    """Erreur métier lors de la récupération d'une police."""


def valider_url_woff2(url: str) -> None:
    """
    Vérifie qu'une URL de téléchargement est HTTPS vers un hôte autorisé.

    Empêche une réponse d'API compromise de faire télécharger un fichier
    depuis un hôte arbitraire.

    Args:
        url (str): URL woff2 fournie par l'API.

    Raises:
        TelechargementPoliceError: Si le schéma ou l'hôte est refusé.
    """
    analyse = urllib.parse.urlparse(url)
    if analyse.scheme != "https":
        raise TelechargementPoliceError(f"Schéma non HTTPS refusé : {url}")
    if analyse.hostname not in HOTES_TELECHARGEMENT_AUTORISES:
        raise TelechargementPoliceError(f"Hôte non autorisé : {url}")


def valider_identifiant_variante(v_id: str) -> None:
    """
    Vérifie le format d'un identifiant de variante issu de l'API.

    L'identifiant sert à construire le nom du fichier local : le motif
    strict exclut tout séparateur de chemin (anti path traversal).

    Args:
        v_id (str): Identifiant de variante (ex : ``600italic``).

    Raises:
        TelechargementPoliceError: Si le format est inattendu.
    """
    if not MOTIF_VARIANTE.fullmatch(v_id):
        raise TelechargementPoliceError(
            f"Identifiant de variante refusé : {v_id!r}"
        )


class _RedirectionValidee(urllib.request.HTTPRedirectHandler):
    """Revalide l'hôte cible à chaque redirection HTTP (défense anti-SSRF)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        # Refuse toute redirection vers un hôte hors de la liste blanche.
        valider_url_woff2(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


# Ouvreur dédié : applique la revalidation d'hôte sur les redirections.
_OUVREUR = urllib.request.build_opener(_RedirectionValidee())


def _lire_limite(flux: object, taille_max: int) -> bytes:
    """
    Lit un flux en refusant les contenus dépassant la taille maximale.

    Args:
        flux: Flux ouvert exposant ``read(taille)``.
        taille_max (int): Nombre d'octets maximal autorisé.

    Returns:
        bytes: Contenu lu (au plus ``taille_max`` octets).

    Raises:
        TelechargementPoliceError: Si le contenu distant dépasse la limite.
    """
    donnees = cast(bytes, flux.read(taille_max + 1))  # type: ignore[attr-defined]
    if len(donnees) > taille_max:
        raise TelechargementPoliceError(
            "Contenu distant trop volumineux : abandon du téléchargement."
        )
    return donnees


def telecharger_fichier(url: str, chemin_destination: Path) -> None:
    """
    Télécharge une URL validée vers un fichier local.

    La récupération est durcie : hôte revérifié à chaque redirection
    (anti-SSRF) et taille de téléchargement bornée.

    Args:
        url (str): URL HTTPS du fichier woff2.
        chemin_destination (Path): Chemin local d'écriture.

    Raises:
        TelechargementPoliceError: Si l'URL est refusée ou le contenu trop gros.
        urllib.error.URLError: En cas d'échec réseau.
        OSError: En cas d'échec d'écriture disque.
    """
    valider_url_woff2(url)
    logger.info(f"Téléchargement de {url} vers {chemin_destination}")
    requete = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with _OUVREUR.open(requete, timeout=TIMEOUT_S) as reponse:
        valider_url_woff2(reponse.geturl())
        chemin_destination.write_bytes(
            _lire_limite(reponse, TAILLE_MAX_TELECHARGEMENT)
        )


def recuperer_metadonnees(font_id: str) -> dict[str, Any]:
    """
    Récupère les métadonnées d'une police auprès de l'API.

    Args:
        font_id (str): Identifiant de la police (clé de ``FONTS_CONFIG``).

    Returns:
        dict[str, Any]: Métadonnées JSON décodées.

    Raises:
        TelechargementPoliceError: Si l'URL/hôte est refusé ou le contenu trop gros.
        urllib.error.URLError: En cas d'échec réseau.
        json.JSONDecodeError: Si la réponse n'est pas du JSON valide.
    """
    url = API_URL_TEMPLATE.format(font_id=font_id)
    valider_url_woff2(url)
    logger.info(f"Récupération des métadonnées : {url}")
    requete = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with _OUVREUR.open(requete, timeout=TIMEOUT_S) as reponse:
        valider_url_woff2(reponse.geturl())
        charge = _lire_limite(reponse, TAILLE_MAX_TELECHARGEMENT)
        donnees = json.loads(charge.decode("utf-8"))
    if not isinstance(donnees, dict):
        raise TelechargementPoliceError(
            "Réponse inattendue de l'API (objet JSON attendu)."
        )
    return donnees


def generer_snippet_css(
    family_name: str, filename: str, font_weight: str, font_style: str
) -> str:
    """
    Construit la règle ``@font-face`` d'une variante téléchargée.

    Args:
        family_name (str): Nom de la famille (constante locale).
        filename (str): Nom du fichier woff2 local.
        font_weight (str): Graisse CSS.
        font_style (str): Style CSS (``normal`` ou ``italic``).

    Returns:
        str: Bloc CSS prêt à être écrit dans ``fonts.css``.
    """
    return f"""@font-face {{
    font-family: '{family_name}';
    src: url('../fonts/{filename}') format('woff2');
    font-weight: {font_weight};
    font-style: {font_style};
    font-display: swap;
}}
"""


def traiter_police(font_id: str, config: dict[str, Any]) -> list[str]:
    """
    Télécharge les variantes d'une police et retourne leurs règles CSS.

    Args:
        font_id (str): Identifiant de la police.
        config (dict[str, Any]): Variantes attendues et nom de famille.

    Returns:
        list[str]: Règles ``@font-face`` générées (vide si échec API).
    """
    family_name: str = config["family_name"]
    variantes_attendues: list[str] = config["variants"]

    try:
        donnees = recuperer_metadonnees(font_id)
    except (urllib.error.URLError, TimeoutError, TelechargementPoliceError) as erreur:
        logger.error(
            f"API injoignable ou refusée pour {font_id} : {erreur}. "
            "Vérifiez la connexion réseau puis relancez le script."
        )
        return []
    except json.JSONDecodeError as erreur:
        logger.error(f"Réponse API invalide pour {font_id} : {erreur}")
        return []

    snippets: list[str] = []
    for variante in donnees.get("variants", []):
        v_id = variante.get("id")
        if v_id not in variantes_attendues:
            continue

        woff2_url = variante.get("woff2")
        if not woff2_url:
            logger.warning(f"Pas d'URL woff2 pour {family_name} ({v_id})")
            continue

        try:
            valider_identifiant_variante(v_id)
            nom_fichier = f"{font_id}-{v_id}.woff2"
            telecharger_fichier(woff2_url, FONTS_DIR / nom_fichier)
        except TelechargementPoliceError as erreur:
            logger.error(f"Variante {v_id} de {family_name} rejetée : {erreur}")
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as erreur:
            logger.error(
                f"Échec du téléchargement de {woff2_url} : {erreur}"
            )
            continue

        font_style = "italic" if "italic" in v_id else "normal"
        font_weight = str(variante.get("fontWeight", "400"))
        snippets.append(
            generer_snippet_css(family_name, nom_fichier, font_weight, font_style)
        )

    return snippets


def main() -> int:
    """
    Télécharge toutes les polices configurées et régénère ``fonts.css``.

    Returns:
        int: 0 si toutes les variantes attendues sont présentes, 1 sinon.
    """
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    CSS_DIR.mkdir(parents=True, exist_ok=True)

    css_content = [
        "/**",
        " * Déclarations des polices Exo 2 et Inter hébergées localement.",
        " * Généré automatiquement par scripts/download_fonts.py.",
        " */",
        "",
    ]

    nb_attendues = sum(len(c["variants"]) for c in FONTS_CONFIG.values())
    nb_obtenues = 0
    for font_id, config in FONTS_CONFIG.items():
        snippets = traiter_police(font_id, config)
        nb_obtenues += len(snippets)
        css_content.extend(snippets)

    if nb_obtenues == 0:
        logger.error("Aucune variante téléchargée : fonts.css non modifié.")
        return 1

    FONTS_CSS_PATH.write_text("\n".join(css_content), encoding="utf-8")
    logger.info(f"Fichier CSS généré : {FONTS_CSS_PATH}")

    if nb_obtenues < nb_attendues:
        logger.warning(
            f"{nb_obtenues}/{nb_attendues} variantes téléchargées : "
            "relancez le script pour compléter."
        )
        return 1

    logger.info(f"{nb_obtenues}/{nb_attendues} variantes téléchargées.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
