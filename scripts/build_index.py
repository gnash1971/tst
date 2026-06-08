"""Assemble index.html à partir de index.template.html et des fragments partials/."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT_DIR / "index.template.html"
OUTPUT_PATH = ROOT_DIR / "index.html"
PARTIAL_PATTERN = re.compile(r"<!--\s*@partial\s+(\S+)\s*-->")
PARTIALS_PREFIX = "partials/"


def valider_chemin_fragment(chemin_relatif: str) -> None:
    """
    Vérifie qu'un fragment reste dans partials/ (anti path traversal).

    Raises:
        ValueError: Si le chemin sort du dossier autorisé.
    """
    normalise = chemin_relatif.replace("\\", "/")
    if ".." in normalise.split("/"):
        raise ValueError(f"Chemin de fragment interdit : {chemin_relatif}")
    if not normalise.startswith(PARTIALS_PREFIX):
        raise ValueError(
            f"Le fragment doit être sous {PARTIALS_PREFIX} : {chemin_relatif}"
        )


def lire_fragment(chemin_relatif: str) -> str:
    """
    Charge un fragment HTML depuis le dossier du projet.

    Args:
        chemin_relatif: Chemin relatif au répertoire racine du site.

    Returns:
        str: Contenu du fragment, sans ligne vide finale superflue.

    Raises:
        FileNotFoundError: Si le fragment est introuvable.
    """
    valider_chemin_fragment(chemin_relatif)
    chemin = ROOT_DIR / chemin_relatif
    if not chemin.is_file():
        raise FileNotFoundError(f"Fragment introuvable : {chemin}")
    return chemin.read_text(encoding="utf-8").rstrip("\n")


def assembler_page(contenu_modele: str) -> str:
    """
    Remplace toutes les directives @partial par le contenu des fragments.

    Args:
        contenu_modele: Contenu brut du fichier modèle.

    Returns:
        str: HTML assemblé prêt à être publié.
    """
    resultat = contenu_modele

    while True:
        correspondance = PARTIAL_PATTERN.search(resultat)
        if correspondance is None:
            break

        fragment = lire_fragment(correspondance.group(1))
        resultat = (
            resultat[: correspondance.start()]
            + fragment
            + resultat[correspondance.end() :]
        )

    return resultat


def construire_index() -> None:
    """Génère index.html à partir du modèle et des fragments."""
    if not TEMPLATE_PATH.is_file():
        print(f"Erreur : modèle introuvable ({TEMPLATE_PATH}).", file=sys.stderr)
        sys.exit(1)

    # Vérifie si le mode production est activé via l'argument --prod
    is_prod = "--prod" in sys.argv

    contenu_modele = TEMPLATE_PATH.read_text(encoding="utf-8")
    contenu_final = assembler_page(contenu_modele)

    if is_prod:
        # En production, on remplace le script du Play CDN de Tailwind par le CSS compilé statique
        cdn_pattern = re.compile(
            r"<!--\s*Tailwind CSS \(CDN\)\s*\+.*-->\s*<script\s+src=\"https://cdn\.tailwindcss\.com\"></script>\s*<script\s+src=\"js/tailwind\.config\.js\"></script>",
            re.IGNORECASE | re.MULTILINE
        )
        remplacement = '<!-- Tailwind CSS statique compilé pour la production -->\n    <link rel="stylesheet" href="css/tailwind.built.css">'
        contenu_final = cdn_pattern.sub(remplacement, contenu_final)

        # On nettoie également la CSP dans la balise <meta> en retirant cdn.tailwindcss.com
        contenu_final = contenu_final.replace(
            "file: https://cdn.tailwindcss.com",
            "file:"
        ).replace(
            " https://cdn.tailwindcss.com",
            ""
        )
        print("Optimisations de production appliquées (Tailwind CDN remplacé par le CSS statique et CSP renforcée).")

    OUTPUT_PATH.write_text(contenu_final + "\n", encoding="utf-8")
    print(f"Page générée : {OUTPUT_PATH}")


if __name__ == "__main__":
    construire_index()
