"""
Script d'assemblage du dossier de production 'dist/'.

Ce script prépare le dossier 'dist/' contenant uniquement les fichiers
nécessaires à la production pour le déploiement sur Netlify ou Apache.
Il évite l'exposition publique de fichiers sensibles comme les scripts,
les fichiers de configuration de build, les sources partielles, etc.
"""

from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path

# Configuration du logging en français
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("build_dist")

# Chemins absolus des répertoires
ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"

def copier_fichier_optionnel(nom_fichier: str) -> None:
    """
    Copie un fichier de la racine vers le dossier dist/ s'il existe.

    Args:
        nom_fichier (str): Nom du fichier à copier.
    """
    src = ROOT_DIR / nom_fichier
    if src.is_file():
        dest = DIST_DIR / nom_fichier
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        logger.info(f"Fichier copié : {nom_fichier}")
    else:
        logger.debug(f"Fichier optionnel absent : {nom_fichier}")

def nettoyer_dossier(dossier: Path) -> None:
    """
    Supprime tout le contenu d'un dossier sans supprimer le dossier lui-même
    pour éviter les verrous de fichiers sur Windows.
    """
    if not dossier.exists():
        return
    for item in dossier.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception as e:
            logger.warning(f"Impossible de supprimer {item} : {e}")

def copier_dossier_optionnel(nom_dossier: str, exlusions: list[str] | None = None) -> None:
    """
    Copie un dossier de la racine vers le dossier dist/ s'il existe.

    Args:
        nom_dossier (str): Nom du dossier à copier.
        exlusions (list[str] | None): Liste de motifs de fichiers à exclure.
    """
    src = ROOT_DIR / nom_dossier
    if src.is_dir():
        dest = DIST_DIR / nom_dossier
        
        # Fonction de filtrage pour ignorer certains fichiers
        def ignore_patterns(path: str, names: list[str]) -> list[str]:
            if exlusions is None:
                return []
            ignored = []
            for name in names:
                for ext in exlusions:
                    if name == ext or name.endswith(ext):
                        ignored.append(name)
            return ignored

        shutil.copytree(src, dest, ignore=ignore_patterns, dirs_exist_ok=True)
        logger.info(f"Dossier copié : {nom_dossier} (avec filtres : {exlusions})")
    else:
        logger.debug(f"Dossier optionnel absent : {nom_dossier}")

def preparer_dossier_production() -> None:
    """
    Orchestre la création et le remplissage du dossier dist/.
    """
    logger.info("Début de la préparation du dossier de production 'dist/'...")

    # 1. Nettoyer ou créer le dossier dist/
    if DIST_DIR.exists():
        logger.info("Nettoyage du contenu du dossier 'dist/'...")
        nettoyer_dossier(DIST_DIR)
    else:
        DIST_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Copier les fichiers de la racine requis pour la production
    fichiers_requis = [
        "index.html",
        "404.html",
        "_headers",
        ".htaccess"
    ]
    for fichier in fichiers_requis:
        copier_fichier_optionnel(fichier)

    # 3. Copier les dossiers requis pour la production
    # On exclut le fichier source CSS d'entrée pour Tailwind
    copier_dossier_optionnel("css", exlusions=["tailwind-input.css"])
    copier_dossier_optionnel("js")
    copier_dossier_optionnel("fonts")
    copier_dossier_optionnel("fic")
    copier_dossier_optionnel("logo")

    logger.info("Préparation du dossier 'dist/' terminée avec succès !")

if __name__ == "__main__":
    try:
        preparer_dossier_production()
    except Exception as e:
        logger.error(f"Une erreur est survenue lors de la préparation de 'dist/' : {e}")
        sys.exit(1)
