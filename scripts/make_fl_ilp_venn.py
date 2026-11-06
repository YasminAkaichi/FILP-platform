"""Generates assets/FILP-venn.svg: Federated Learning + ILP = FILP (with the FILP flower).

Same palette as the Home pipeline figure. Run:  python scripts/make_fl_ilp_venn.py
"""
from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

FONT = "Inter, 'Source Sans 3', 'Segoe UI', Helvetica, Arial, sans-serif"
NAVY, INK, MUTED = "#11026D", "#1F2430", "#5B6472"
VIOLET, VIOLET_FILL = "#7C5CC4", "#EDE8F8"
BLUE, BLUE_FILL = "#2F6FBF", "#E3EDF9"

W, H = 1200, 800
R, CY = 320, 400
CX_L, CX_R = 450, 750


def flower_data_uri() -> str:
    img = Image.open(ASSETS / "filp_logo_navy.png").convert("RGBA")
    w, h = img.size
    img = img.crop((0, 0, w, int(h * 0.83)))  # the flower only, without the word "FILP"
    img.thumbnail((360, 360))
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def build() -> str:
    left = f"M {CX_L - R} {CY} a {R} {R} 0 1 0 {2 * R} 0 a {R} {R} 0 1 0 {-2 * R} 0 Z"
    right = f"M {CX_R - R} {CY} a {R} {R} 0 1 0 {2 * R} 0 a {R} {R} 0 1 0 {-2 * R} 0 Z"
    mid = (CX_L + CX_R) / 2

    def t(x, y, text, size, color, weight=600, spacing=0):
        return (
            f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{size}" '
            f'font-weight="{weight}" letter-spacing="{spacing}" fill="{color}">{text}</text>'
        )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}" '
        'style="width:100%;height:auto;display:block;">',
        f'<defs><clipPath id="filpVennL"><path d="{left}"/></clipPath></defs>',
        f'<path d="{left}" fill="{VIOLET_FILL}"/>',
        f'<path d="{right}" fill="{BLUE_FILL}"/>',
        f'<path d="{right}" fill="{NAVY}" fill-opacity="0.10" clip-path="url(#filpVennL)"/>',
        f'<path d="{left}" fill="none" stroke="{VIOLET}" stroke-width="6"/>',
        f'<path d="{right}" fill="none" stroke="{BLUE}" stroke-width="6"/>',
        # left circle
        t(285, 345, "Federated", 44, VIOLET, 700),
        t(285, 405, "Learning", 44, VIOLET, 700),
        t(285, 465, "privacy · local data", 26, MUTED, 500),
        # right circle
        t(918, 310, "Inductive", 44, BLUE, 700),
        t(918, 370, "Logic", 44, BLUE, 700),
        t(918, 430, "Programming", 44, BLUE, 700),
        t(918, 490, "rules · explainable", 26, MUTED, 500),
        # intersection: logo + name
        f'<image href="{flower_data_uri()}" x="{mid - 85}" y="{CY - 175}" width="170" height="170" '
        'preserveAspectRatio="xMidYMid meet"/>',
        t(mid, CY + 70, "FILP", 64, NAVY, 800, 3),
        "</svg>",
    ]
    return "\n".join(parts)


if __name__ == "__main__":
    out = ASSETS / "FILP-venn.svg"
    out.write_text(build(), encoding="utf-8")
    print("written", out, out.stat().st_size // 1024, "KB")
