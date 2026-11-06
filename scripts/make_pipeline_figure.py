"""Draws the FILP pipeline figure (assets/FILP-pipeline.svg).

    python scripts/make_pipeline_figure.py

The figure is generated, so the wording and the colours are edited here and the
file is rebuilt. It shows the three approaches of the thesis in the 'Federated
ILP' stage: Consensus (the clients learn, the server votes) and Coordination /
Collaboration (the server generates candidates, the clients only test them, in
rounds).
"""

from __future__ import annotations

import textwrap
from html import escape
from pathlib import Path

W, H = 1800, 900
FONT = "Inter, 'Source Sans 3', 'Segoe UI', Helvetica, Arial, sans-serif"

NAVY, CREAM, INK, MUTED = "#11026D", "#F0EADD", "#1F2430", "#5B6472"
STAGE = {  # header colour, body tint
    "data": ("#11026D", "#EEF1FA"),
    "prep": ("#11026D", "#EEF1FA"),
    "fed": ("#11026D", "#F5F3FB"),
    "eval": ("#11026D", "#EEF1FA"),
    "res": ("#11026D", "#EEF1FA"),
}
LANE = {
    "consensus": ("#7C5CC4", "#EDE8F8"),
    "coordination": ("#2F6FBF", "#E3EDF9"),
    "collaboration": ("#C0613F", "#F9E9E2"),
}

out: list[str] = []


def add(s: str) -> None:
    out.append(s)


def text(x, y, s, size=21, weight=400, fill=INK, anchor="start", italic=False):
    style = ' font-style="italic"' if italic else ""
    add(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}"{style}>{escape(s)}</text>')


def wrapped(x, y, s, width_px, size=21, weight=400, fill=INK, line=1.32, anchor="start"):
    chars = max(8, int(width_px / (size * 0.53)))
    lines = textwrap.wrap(s, chars) or [""]
    for i, l in enumerate(lines):
        text(x, y + i * size * line, l, size, weight, fill, anchor)
    return y + len(lines) * size * line


def rect(x, y, w, h, fill, stroke="none", r=18, sw=2):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def arrow(x1, y1, x2, y2, color=NAVY, sw=3.2):
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" marker-end="url(#head-{color[1:]})"/>')


def db_icon(cx, cy, w=64, h=70, color=NAVY):
    rx, ry = w / 2, 11
    top, bot = cy - h / 2, cy + h / 2
    add(f'<path d="M{cx-rx} {top} V{bot} A{rx} {ry} 0 0 0 {cx+rx} {bot} V{top}" fill="{color}"/>')
    add(f'<ellipse cx="{cx}" cy="{top}" rx="{rx}" ry="{ry}" fill="{color}"/>')
    for k in (1, 2):
        yy = top + k * h / 3
        add(f'<path d="M{cx-rx} {yy} A{rx} {ry} 0 0 0 {cx+rx} {yy}" fill="none" stroke="{CREAM}" stroke-width="3"/>')


def bullets(x, y, items, width_px, size=20, color=NAVY):
    for it in items:
        add(f'<circle cx="{x+6}" cy="{y-7}" r="4.2" fill="{color}"/>')
        y = wrapped(x + 22, y, it, width_px - 22, size=size) + 9
    return y


def column(x, w, num, title, sub, kind):
    head, tint = STAGE[kind]
    rect(x, 150, w, 700, tint, r=20)
    add(f'<path d="M{x} 210 V170 Q{x} 150 {x+20} 150 H{x+w-20} Q{x+w} 150 {x+w} 170 V210 Z" fill="{head}"/>')
    add(f'<circle cx="{x+30}" cy="180" r="15" fill="{CREAM}"/>')
    text(x + 30, 187, str(num), 19, 700, NAVY, "middle")
    text(x + 56, 188, title, 24, 700, CREAM)
    if sub:
        wrapped(x + 22, 246, sub, w - 44, size=19, fill=MUTED)


def chevron(x, y):
    add(f'<path d="M{x} {y-18} L{x+16} {y} L{x} {y+18}" fill="none" stroke="{NAVY}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')


# ----------------------------------------------------------------- canvas
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}">')
add("<defs>")
for c in (NAVY, LANE["consensus"][0], LANE["coordination"][0], LANE["collaboration"][0]):
    add(f'<marker id="head-{c[1:]}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M1 1 L9 5 L1 9 Z" fill="{c}"/></marker>')
add("</defs>")
rect(0, 0, W, H, "#FFFFFF", r=0)
rect(15, 15, W - 30, 120, "#F3F4F8", r=22)
text(48, 78, "FILP pipeline", 52, 800, NAVY)
text(48, 116, "From a dataset to interpretable hypotheses. The clients are simulated on one machine, and no example leaves a client.", 23, 400, MUTED)

# ----------------------------------------------------------- 1 datasets
X1, W1 = 30, 250
column(X1, W1, 1, "Datasets", "Pick a task, or bring your own.", "data")
db_icon(X1 + W1 / 2, 345)
text(X1 + 22, 430, "Built-in", 21, 700, NAVY)
y = bullets(X1 + 22, 462, ["Zendo1", "Trains1000", "IGGP-RPS", "Synthesis-sorted", "Breast cancer", "Intubation"], W1 - 44)
text(X1 + 22, y + 22, "Your own data", 21, 700, NAVY)
wrapped(X1 + 22, y + 52, "A table (CSV) turned into an ILP task (Custom ILP).", W1 - 44, size=19)

# ------------------------------------------------------ 2 preparation
X2, W2 = 300, 270
column(X2, W2, 2, "Data preparation", "The data are split into private shares.", "prep")
# three small client shares
for i, c in enumerate(("#7C5CC4", "#2F6FBF", "#C0613F")):
    db_icon(X2 + 70 + i * 66, 345, w=44, h=52, color=c)
y = bullets(X2 + 22, 430, ["The examples are divided among K clients", "IID or non-IID partitions", "A seed makes it reproducible", "Consensus only: a train / test split"], W2 - 44)
rect(X2 + 18, y + 12, W2 - 36, 64, "#FFFFFF", "#D6DAE6", r=14, sw=1.5)
wrapped(X2 + 32, y + 40, "Simulated clients on the local machine", W2 - 64, size=18, fill=MUTED)

# ------------------------------------------------------ 3 federated ILP
X3, W3 = 590, 770
column(X3, W3, 3, "Federated ILP", "", "fed")
CX, CW = X3 + 20, 330          # clients column
SX, SW = X3 + 20 + CW + 70, 330  # server column
text(CX + CW / 2, 250, "Clients (private data)", 20, 700, MUTED, "middle")
text(SX + SW / 2, 250, "Server", 20, 700, MUTED, "middle")

lanes = [
    ("consensus", "Learning by Consensus", "Popper 4 or Andante",
     "Each client learns its own hypothesis Hᵢ", "Collects the Hᵢ and takes the majority vote", False),
    ("coordination", "Learning by Coordination", "Bach store · Popper 1.1.0",
     "Test the candidate on local data", "Generates a candidate, aggregates the outcomes, adds constraints", True),
    ("collaboration", "Learning by Collaboration", "Flower · Popper 1.1.0",
     "Test the candidate on local data", "Generates a candidate, aggregates the outcomes, adds constraints", True),
]
LY, LH, GAP = 266, 180, 12
for i, (key, name, infra, cl, sv, loop) in enumerate(lanes):
    color, tint = LANE[key]
    y0 = LY + i * (LH + GAP)
    rect(X3 + 10, y0, W3 - 20, LH, tint, r=16)
    add(f'<rect x="{X3+10}" y="{y0}" width="9" height="{LH}" rx="4" fill="{color}"/>')
    text(CX + 14, y0 + 34, name, 22, 700, color)
    text(X3 + W3 - 28, y0 + 34, infra, 18, 500, MUTED, "end")
    by, bh = y0 + 52, 102
    rect(CX + 8, by, CW - 16, bh, "#FFFFFF", color, r=14, sw=2)
    wrapped(CX + 26, by + 38, cl, CW - 52, size=20)
    rect(SX + 8, by, SW - 16, bh, "#FFFFFF", color, r=14, sw=2)
    wrapped(SX + 26, by + 38, sv, SW - 52, size=20)
    mid = CX + CW - 8
    ax1, ax2 = mid + 6, SX + 2
    if loop:
        arrow(ax2, by + 38, ax1, by + 38, color)            # server -> clients
        text((ax1 + ax2) / 2, by + 26, "candidate", 15, 500, color, "middle")
        arrow(ax1, by + 74, ax2, by + 74, color)            # clients -> server
        text((ax1 + ax2) / 2, by + 98, "outcome", 15, 500, color, "middle")
        text(X3 + W3 / 2 + 6, y0 + LH - 9, "repeated round after round, until a solution is found", 16, 500, color, "middle", italic=True)
    else:
        arrow(ax1, by + 56, ax2, by + 56, color)
        text((ax1 + ax2) / 2, by + 42, "Hᵢ", 17, 600, color, "middle")

# --------------------------------------------------------- 4 evaluation
X4, W4 = 1380, 200
column(X4, W4, 4, "Evaluation", "The same questions for every approach.", "eval")
bullets(X4 + 20, 450, [
    "Accuracy and MCC (Consensus)",
    "Same programs as a centralized search (client 0)",
    "Centralized Popper as a baseline",
    "Learning time and messages",
], W4 - 36, size=19)
# little bar chart icon
for i, hgt in enumerate((26, 42, 58)):
    add(f'<rect x="{X4+W4/2-34+i*26}" y="{400-hgt}" width="18" height="{hgt}" rx="3" fill="{NAVY}"/>')

# ------------------------------------------------------------ 5 results
X5, W5 = 1600, 175
column(X5, W5, 5, "Results", "Readable by design.", "res")
bullets(X5 + 18, 450, [
    "Hypotheses as logic programs",
    "The vote of every client",
    "One final program",
    "Dashboards and history",
], W5 - 32, size=19)
# little document icon
add(f'<rect x="{X5+W5/2-24}" y="340" width="48" height="58" rx="6" fill="none" stroke="{NAVY}" stroke-width="4"/>')
for k in range(3):
    add(f'<line x1="{X5+W5/2-12}" y1="{354+k*12}" x2="{X5+W5/2+12}" y2="{354+k*12}" stroke="{NAVY}" stroke-width="3.5" stroke-linecap="round"/>')

# ----------------------------------------------------------- chevrons
for cx in (X1 + W1 + 10, X2 + W2 + 10, X3 + W3 + 10, X4 + W4 + 10):
    chevron(cx - 2, 500)

# ------------------------------------------------------------- footer
rect(15, 862, W - 30, 28, "#F3F4F8", r=14)
text(W / 2, 882, "Only hypotheses or symbolic outcomes travel between the clients and the server: raw examples stay where they are.", 18, 500, NAVY, "middle")
add("</svg>")

target = Path(__file__).resolve().parents[1] / "assets" / "FILP-pipeline.svg"
target.write_text("\n".join(out), encoding="utf-8")
print("written", target)
