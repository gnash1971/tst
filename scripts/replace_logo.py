"""Remplace le logo inline dans les documents HTML du club LTT."""

import base64
import re
from pathlib import Path

LOGO_PATH = Path(r"h:\Mon Drive\ENSBAL\clubTTLentilly\V4_logoLTT_RVB.png")
HTML_DIR = Path(r"h:\Mon Drive\ENSBAL\clubTTLentilly")

FILES: dict[str, tuple[int, int]] = {
    "V2_PV_AG1.html": (117, 64),
    "V2_fiche_inscription.html": (117, 64),
    "V5_reglement_interieur_clubLTT.html": (132, 72),
    "V12_statuts_club_LTT.html": (132, 72),
}

logo_b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
new_src = f"data:image/jpeg;base64,{logo_b64}"

img_pattern = re.compile(
    r'(<img\s+class="doc-header__icon"\s+src=")'
    r"data:image/[^;]+;base64,[^\"]+"
    r'("\s+width=")\d+("\s+height=")\d+'
    r'("\s+alt="Logo du club Lentilly Tennis de Table"\s*>)',
    re.DOTALL,
)

css_pattern_64 = re.compile(
    r"(\.doc-header__icon\s*\{[^}]*?width:\s*)64px(\s*;\s*height:\s*)64px",
    re.DOTALL,
)


def main() -> None:
    """Remplace le logo et ajuste les dimensions dans chaque fichier HTML."""
    for filename, (width, height) in FILES.items():
        path = HTML_DIR / filename
        content = path.read_text(encoding="utf-8")
        new_content, count = img_pattern.subn(
            rf"\g<1>{new_src}\g<2>{width}\g<3>{height}\g<4>",
            content,
        )
        if count != 1:
            raise SystemExit(f"{filename}: {count} remplacements img (attendu 1)")

        if width == 117 and height == 64:
            new_content, css_count = css_pattern_64.subn(
                rf"\g<1>{width}px\g<2>{height}px",
                new_content,
            )
            if css_count:
                print(f"{filename}: CSS mis à jour ({css_count} occurrence(s))")

        path.write_text(new_content, encoding="utf-8")
        print(f"{filename}: logo remplacé ({width}×{height})")

    print("Terminé.")


if __name__ == "__main__":
    main()
