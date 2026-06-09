import json
import os
import urllib.request
from pathlib import Path

# Chemins absolus
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = PROJECT_ROOT / "fonts"
CSS_DIR = PROJECT_ROOT / "css"
FONTS_CSS_PATH = CSS_DIR / "fonts.css"

# Configuration des polices à télécharger
FONTS_CONFIG = {
    "exo-2": {
        "variants": ["600", "700", "800", "600italic"],
        "family_name": "Exo 2"
    },
    "inter": {
        "variants": ["regular", "500", "600", "700", "800"],
        "family_name": "Inter"
    }
}

def download_file(url: str, dest_path: Path) -> None:
    print(f"Téléchargement de {url} vers {dest_path}...")
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    with urllib.request.urlopen(req) as response:
        dest_path.write_bytes(response.read())

def main() -> None:
    # Créer le dossier fonts s'il n'existe pas
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    CSS_DIR.mkdir(parents=True, exist_ok=True)

    css_content = [
        "/**",
        " * Déclarations des polices Exo 2 et Inter hébergées localement.",
        " * Généré automatiquement par scripts/download_fonts.py.",
        " */",
        ""
    ]

    for font_id, config in FONTS_CONFIG.items():
        family_name = config["family_name"]
        variants = config["variants"]
        
        # Récupérer les métadonnées de la police
        url = f"https://gwfh.mranftl.com/api/fonts/{font_id}?subsets=latin"
        print(f"Récupération des métadonnées pour {family_name} ({url})...")
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"Erreur lors de la récupération de {font_id} : {e}")
            continue

        # Parcourir les variantes de la police
        for variant in data.get("variants", []):
            v_id = variant.get("id")
            if v_id not in variants:
                continue
            
            # Déterminer les propriétés CSS
            font_style = "italic" if "italic" in v_id else "normal"
            font_weight = variant.get("fontWeight", "400")
            
            # Télécharger le fichier woff2
            woff2_url = variant.get("woff2")
            if not woff2_url:
                print(f"Pas d'URL woff2 pour la variante {v_id} de {family_name}")
                continue
            
            # Nom du fichier de destination
            file_extension = "woff2"
            filename = f"{font_id}-{v_id}.{file_extension}"
            dest_file_path = FONTS_DIR / filename
            
            # Télécharger le fichier
            try:
                download_file(woff2_url, dest_file_path)
            except Exception as e:
                print(f"Erreur lors du téléchargement de {woff2_url} : {e}")
                continue
            
            # Ajouter la règle @font-face au CSS
            css_snippet = f"""@font-face {{
    font-family: '{family_name}';
    src: url('../fonts/{filename}') format('woff2');
    font-weight: {font_weight};
    font-style: {font_style};
    font-display: swap;
}}
"""
            css_content.append(css_snippet)

    # Écrire le fichier css/fonts.css
    FONTS_CSS_PATH.write_text("\n".join(css_content), encoding="utf-8")
    print(f"Fichier CSS généré avec succès : {FONTS_CSS_PATH}")

if __name__ == "__main__":
    main()
