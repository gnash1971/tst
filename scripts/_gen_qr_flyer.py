"""Génère les QR codes locaux pour le flyer LTT (PNG haute résolution + SVG)."""

from __future__ import annotations

from pathlib import Path

import qrcode
import qrcode.constants
from qrcode.image.svg import SvgPathImage

URL = "https://www.l-tt.club"
FILL = "#064e3b"
PUB = Path(r"h:\Mon Drive\ENSBAL\clubTTLentilly\pub")


def main() -> None:
    """Crée qr_l-tt-club.png et qr_l-tt-club.svg dans pub/."""
    qr_png = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=24,
        border=2,
    )
    qr_png.add_data(URL)
    qr_png.make(fit=True)
    img = qr_png.make_image(fill_color=FILL, back_color="white")
    png_path = PUB / "qr_l-tt-club.png"
    img.save(png_path)
    print(f"PNG {img.size[0]}x{img.size[1]} -> {png_path}")

    qr_svg = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr_svg.add_data(URL)
    qr_svg.make(fit=True)
    svg_img = qr_svg.make_image(image_factory=SvgPathImage)
    svg_path = PUB / "qr_l-tt-club.svg"
    svg_img.save(svg_path)
    text = svg_path.read_text(encoding="utf-8")
    text = text.replace('fill="#000000"', f'fill="{FILL}"')
    text = text.replace('stroke="#000000"', f'stroke="{FILL}"')
    svg_path.write_text(text, encoding="utf-8")
    print(f"SVG -> {svg_path} ({svg_path.stat().st_size} octets)")


if __name__ == "__main__":
    main()
