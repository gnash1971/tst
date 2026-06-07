"""Corrige le type MIME du logo (JPEG encodé avec extension .png)."""

from pathlib import Path

HTML_DIR = Path(r"h:\Mon Drive\ENSBAL\clubTTLentilly")
FILES = [
    "V2_PV_AG1.html",
    "V2_fiche_inscription.html",
    "V5_reglement_interieur_clubLTT.html",
    "V12_statuts_club_LTT.html",
]

OLD = "data:image/png;base64,/9j/"
NEW = "data:image/jpeg;base64,/9j/"

for name in FILES:
    path = HTML_DIR / name
    content = path.read_text(encoding="utf-8")
    if OLD not in content:
        raise SystemExit(f"{name}: motif MIME introuvable")
    path.write_text(content.replace(OLD, NEW, 1), encoding="utf-8")
    print(f"{name}: MIME corrigé")
