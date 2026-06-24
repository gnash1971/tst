"""Assemble index.html depuis le modèle, les fragments partials/ et les données.

Deux directives sont reconnues dans index.template.html :

- ``<!-- @partial partials/xxx.html -->`` : inclusion d'un fragment statique ;
- ``<!-- @documents -->`` : rendu des cartes documentaires depuis
  data/documents.json via le gabarit Jinja2 templates/doc-card.html.j2.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# ``models`` est un module voisin (dossier scripts/), présent sur sys.path à
# l'exécution (python scripts/build_index.py) comme en test (via conftest).
from models import DocumentsConfigError, charger_documents

ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT_DIR / "index.template.html"
OUTPUT_PATH = ROOT_DIR / "index.html"
DATA_PATH = ROOT_DIR / "data" / "documents.json"
TEMPLATES_DIR = ROOT_DIR / "templates"
CARD_TEMPLATE_NAME = "doc-card.html.j2"
BRAND_THEME_PATH = ROOT_DIR / "data" / "brand-theme.json"
JS_TAILWIND_CONFIG_PATH = ROOT_DIR / "js" / "tailwind.config.js"
PARTIAL_PATTERN = re.compile(r"<!--\s*@partial\s+(\S+)\s*-->")
DOCUMENTS_PATTERN = re.compile(r"<!--\s*@documents\s*-->")
PARTIALS_PREFIX = "partials/"

# Bloc Tailwind CDN (mode développement) remplacé en production.
CDN_PATTERN = re.compile(
    r"<!--\s*Tailwind CSS \(CDN\)\s*\+.*-->\s*"
    r"<script\s+src=\"https://cdn\.tailwindcss\.com\"></script>\s*"
    r"<script\s+src=\"js/tailwind\.config\.js\"></script>",
    re.IGNORECASE | re.MULTILINE,
)
REMPLACEMENT_CSS_STATIQUE = (
    "<!-- Tailwind CSS statique compilé pour la production -->\n"
    '    <link rel="stylesheet" href="css/tailwind.built.css">'
)


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


def rendre_cartes_documents() -> str:
    """
    Rend les cartes documentaires depuis data/documents.json.

    Chaque entrée validée (Pydantic) est passée au gabarit Jinja2
    ``templates/doc-card.html.j2``. L'auto-échappement est désactivé car le
    contenu provient d'une source maîtrisée et versionnée (pas d'entrée
    utilisateur) et certains champs contiennent du HTML volontaire.

    Returns:
        str: Bloc HTML des cartes, séparées par un saut de ligne.

    Raises:
        DocumentsConfigError: Si les données sont absentes ou non conformes.
    """
    documents = charger_documents(DATA_PATH)
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=False,
    )
    gabarit = env.get_template(CARD_TEMPLATE_NAME)
    cartes = [gabarit.render(**doc.model_dump()).rstrip("\n") for doc in documents]
    return "\n".join(cartes)


def injecter_documents(contenu: str) -> str:
    """
    Remplace la directive ``<!-- @documents -->`` par les cartes rendues.

    Args:
        contenu: HTML assemblé (après résolution des @partial).

    Returns:
        str: HTML avec les cartes documentaires injectées. Inchangé si la
            directive est absente.

    Raises:
        DocumentsConfigError: Si les données sont absentes ou non conformes.
    """
    if DOCUMENTS_PATTERN.search(contenu) is None:
        return contenu

    cartes = rendre_cartes_documents()
    # ``lambda`` pour éviter l'interprétation des antislashs/groupes par re.sub.
    return DOCUMENTS_PATTERN.sub(lambda _correspondance: cartes, contenu, count=1)


def generer_config_tailwind_cdn() -> None:
    """
    Génère js/tailwind.config.js depuis data/brand-theme.json.

    Le Play CDN (mode développement) et le CLI Tailwind (tailwind.config.js
    racine, via ``require``) partagent ainsi une source de thème unique, ce
    qui supprime tout risque de divergence des couleurs/polices.

    Le fichier produit est un artefact : il ne doit pas être édité à la main.
    """
    if not BRAND_THEME_PATH.is_file():
        print(
            f"Avertissement : thème introuvable ({BRAND_THEME_PATH}).",
            file=sys.stderr,
        )
        return

    theme = json.loads(BRAND_THEME_PATH.read_text(encoding="utf-8"))
    config = {"darkMode": "class", "theme": {"extend": theme}}
    corps = json.dumps(config, indent=4, ensure_ascii=False)
    contenu = (
        "/*\n"
        " * Configuration Tailwind du Play CDN (mode développement).\n"
        " * FICHIER GÉNÉRÉ par scripts/build_index.py depuis"
        " data/brand-theme.json.\n"
        " * Ne pas éditer à la main : modifier data/brand-theme.json puis\n"
        " * régénérer (python scripts/build_index.py).\n"
        " * À charger après https://cdn.tailwindcss.com.\n"
        " */\n"
        f"tailwind.config = {corps};\n"
    )
    JS_TAILWIND_CONFIG_PATH.write_text(contenu, encoding="utf-8")
    print(f"Config Tailwind CDN générée : {JS_TAILWIND_CONFIG_PATH}")


def appliquer_optimisations_production(contenu: str) -> str:
    """
    Applique les transformations de production au HTML assemblé.

    Remplace le Play CDN de Tailwind par le CSS compilé statique et retire
    cdn.tailwindcss.com de la CSP déclarée en balise ``<meta>``.

    Args:
        contenu: HTML assemblé en mode développement.

    Returns:
        str: HTML prêt pour la publication (sans dépendance CDN).
    """
    resultat = CDN_PATTERN.sub(REMPLACEMENT_CSS_STATIQUE, contenu)
    resultat = resultat.replace('href="css/styles.css"', 'href="css/styles.built.css"')
    resultat = resultat.replace("file: https://cdn.tailwindcss.com", "file:")
    return resultat.replace(" https://cdn.tailwindcss.com", "")


def assembler_styles_production() -> None:
    """
    Lit css/styles.css, résout et fusionne tous les @import locaux dans css/styles.built.css.
    """
    css_dir = ROOT_DIR / "css"
    styles_src = css_dir / "styles.css"
    styles_dest = css_dir / "styles.built.css"

    if not styles_src.is_file():
        print(f"Avertissement : styles.css introuvable ({styles_src}).", file=sys.stderr)
        return

    print("Concaténation et minification des styles personnalisés de production...")
    contenu_source = styles_src.read_text(encoding="utf-8")
    
    # Recherche des déclarations d'importation sous forme : @import url('...') ou @import "..."
    import_pattern = re.compile(r"@import\s+(?:url\()?['\"]?([^'\"#\s\)]+)['\"]?\)?\s*;")
    
    contenu_built = []
    
    for ligne in contenu_source.splitlines():
        correspondance = import_pattern.search(ligne)
        if correspondance:
            nom_fichier = correspondance.group(1)
            fichier_cible = css_dir / nom_fichier
            if fichier_cible.is_file():
                # Lecture et injection du contenu du sous-fichier
                print(f"  -> Concaténation de : {nom_fichier}")
                css_file_content = fichier_cible.read_text(encoding="utf-8")
                # Petite minification basique (retrait des commentaires block et des lignes vides)
                css_file_content = re.sub(r'/\*[\s\S]*?\*/', '', css_file_content)
                contenu_built.append(f"\n/* --- DEBUT {nom_fichier} --- */\n{css_file_content.strip()}")
            else:
                print(f"Avertissement : Fichier importé introuvable : {nom_fichier}", file=sys.stderr)
        else:
            # On conserve les règles éventuellement définies directement dans styles.css (hors imports)
            ligne_strip = ligne.strip()
            if ligne_strip and not ligne_strip.startswith("/*"):
                contenu_built.append(ligne)
                
    # Écrit le résultat final fusionné et minifié
    styles_dest.write_text("\n".join(contenu_built) + "\n", encoding="utf-8")
    print(f"Fichier de styles compilé créé : {styles_dest}")


def construire_index() -> None:
    """Génère index.html à partir du modèle et des fragments."""
    if not TEMPLATE_PATH.is_file():
        print(f"Erreur : modèle introuvable ({TEMPLATE_PATH}).", file=sys.stderr)
        sys.exit(1)

    # Vérifie si le mode production est activé via l'argument --prod
    is_prod = "--prod" in sys.argv

    # Régénère la config Tailwind du CDN depuis la source de thème unique.
    generer_config_tailwind_cdn()

    contenu_modele = TEMPLATE_PATH.read_text(encoding="utf-8")
    contenu_final = assembler_page(contenu_modele)

    try:
        contenu_final = injecter_documents(contenu_final)
    except DocumentsConfigError as exc:
        print(f"Erreur de configuration des documents : {exc}", file=sys.stderr)
        sys.exit(1)

    if is_prod:
        # 1. Générer le fichier de style concaténé et minifié styles.built.css
        assembler_styles_production()
        
        # 2. Remplacer les appels CDN et styles.css de développement par les versions de production
        contenu_final = appliquer_optimisations_production(contenu_final)
        print(
            "Optimisations de production appliquées (Tailwind CDN remplacé "
            "par le CSS statique et CSP renforcée)."
        )

    OUTPUT_PATH.write_text(contenu_final + "\n", encoding="utf-8")
    print(f"Page générée : {OUTPUT_PATH}")


if __name__ == "__main__":
    construire_index()
