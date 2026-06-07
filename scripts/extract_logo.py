"""Script temporaire pour extraire le logo du club depuis l'un des documents officiels HTML."""

import base64
import re
from pathlib import Path

# Chemins des fichiers
DIR_PATH = Path(r"h:\Mon Drive\ENSBAL\clubTTLentilly")
HTML_FILE = DIR_PATH / "V2_fiche_inscription.html"
OUTPUT_LOGO = DIR_PATH / "logo_club.jpg"

def extraire_logo() -> None:
    """Extrait l'image en base64 présente dans le fichier HTML et la sauvegarde sous forme de fichier JPEG."""
    if not HTML_FILE.exists():
        print(f"Erreur : Le fichier {HTML_FILE} n'existe pas.")
        return

    content = HTML_FILE.read_text(encoding="utf-8")
    
    # Recherche du motif de données base64 de l'image jpeg ou png
    match = re.search(r'data:image/(?:jpeg|png);base64,([A-Za-z0-9+/=\s]+)', content)
    if not match:
        print("Erreur : Aucun motif de logo en base64 trouvé dans le HTML.")
        return

    # Nettoyage du base64 (suppression des espaces ou retours à la ligne potentiels)
    b64_data = re.sub(r'\s+', '', match.group(1))
    
    # Décodage et écriture du fichier
    try:
        image_bytes = base64.b64decode(b64_data)
        OUTPUT_LOGO.write_bytes(image_bytes)
        print(f"Succès : Le logo a été extrait et sauvegardé dans {OUTPUT_LOGO}")
    except Exception as e:
        print(f"Erreur lors du décodage ou de l'écriture : {e}")

if __name__ == "__main__":
    extraire_logo()
