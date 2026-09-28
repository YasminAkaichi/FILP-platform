from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------
# Project setup
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_connection

DATASETS_DIRECTORY = PROJECT_ROOT / "datasets"


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Inductive logic programming | FILP",
    page_icon=":material/psychology:",
    layout="wide",
)

if hasattr(st, "logo"):
    try:
        st.logo(str(PROJECT_ROOT / "assets" / "filp_wordmark_white.svg"), size="large")
    except Exception:
        pass




# ---------------------------------------------------------------------
# Visual design system
# ---------------------------------------------------------------------

PALETTE = {
    "bg_card": "#F6F8FC",
    "border": "#E2E8F5",
    "text_muted": "#5B6472",
    "text": "#1F2430",
    "primary": "#3E63DE",
    "primary_soft": "#EAF0FE",
    "success": "#2F9E63",
    "success_soft": "#E7F6EE",
    "warning": "#C98A1F",
    "warning_soft": "#FCF1DE",
    "error": "#D1554B",
    "error_soft": "#FBEAE8",
    "neutral": "#8A93A3",
    "neutral_soft": "#EEF1F6",
    "progol": "#7C5CFC",
    "progol_soft": "#F1ECFE",
    "popper": "#3E7BFA",
    "popper_soft": "#E8F0FE",
}

SIZE_STYLE = {
    "Small": (PALETTE["success"], PALETTE["success_soft"]),
    "Medium": (PALETTE["warning"], PALETTE["warning_soft"]),
    "Large": (PALETTE["error"], PALETTE["error_soft"]),
}

COLOR_SWATCH = {
    "red": "#D1554B",
    "blue": "#3E7BFA",
    "green": "#2F9E63",
}

COLOR_EMOJI = {
    "red": "🔴",
    "blue": "🔵",
    "green": "🟢",
}

DATASET_BLURBS = {
    "zendo1": "Zendo scene classification — a table of geometric pieces, learn the hidden rule an arrangement must satisfy.",
    "trains": "The classic Michalski trains — classify eastbound vs westbound trains from their car properties.",
    "trains1": "Michalski trains, variant 1.",
    "trains2": "Michalski trains, extended variant with more cars and attributes.",
    "trains1000": "Michalski trains at scale — 1000 generated trains.",
    "synthesis-sorted": "Program-synthesis style task: learn what makes a list \"sorted\".",
    "iggp-rps": "General Game Playing — Rock-Paper-Scissors legal-move / outcome relations.",
}

SHORT_DATASET_BLURBS = {
    "zendo1": "Geometric scene rules",
    "trains": "Classic Michalski trains",
    "trains1": "Michalski trains variant",
    "trains2": "Extended trains dataset",
    "trains1000": "Large-scale trains",
    "synthesis-sorted": "Sorted-list synthesis",
    "iggp-rps": "Rock-paper-scissors relations",
}


def inject_style() -> None:
    # NOTE: every hand-written HTML snippet below is a single line
    # with no leading indentation — a blank line followed by 4+
    # spaces of indentation is read as a code block by Streamlit's
    # markdown renderer, which silently breaks custom HTML cards.
    st.markdown(
        f"""
        <style>
        .block-container {{
            padding-top: 3rem;
            padding-bottom: 3rem;
            padding-left: 2.2rem;
            padding-right: 2.2rem;
            max-width: 100% !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 14px !important;
        }}

        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {PALETTE["primary"]} !important;
        }}
        div[data-baseweb="tab-highlight"] {{
            background-color: {PALETTE["primary"]} !important;
        }}
        div[data-baseweb="tab-border"] {{
            background-color: {PALETTE["border"]} !important;
        }}

        .breadcrumb {{
            font-size: 0.85rem;
            color: {PALETTE["text_muted"]};
            margin-bottom: 4px;
        }}

        .ilp-banner {{
            height: 100%;
            display: flex;
            gap: 12px;
            align-items: flex-start;
            padding: 1rem 1.2rem;
            border-radius: 14px;
            background: {PALETTE["warning_soft"]};
            border: 1px solid #F0DCB4;
        }}
        .ilp-banner .banner-icon {{ display: flex; align-items: flex-start; flex-shrink: 0; padding-top: 2px; }}
        .ilp-banner .banner-body {{ color: {PALETTE["text"]}; font-size: 1.05rem; line-height: 1.55; }}

        .section-title {{
            font-size: 1.05rem;
            font-weight: 700;
            color: {PALETTE["text"]};
            margin: 0 0 4px 0;
        }}
        .section-caption {{
            font-size: 0.85rem;
            color: {PALETTE["text_muted"]};
            margin-bottom: 10px;
        }}
        .katex-display {{
            margin: 0.6rem 0 !important;
        }}

        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 11px;
            border-radius: 999px;
            font-size: 0.76rem;
            font-weight: 700;
        }}

        .dataset-card {{
            padding: 12px 14px;
            border-radius: 12px;
            border: 1.5px solid {PALETTE["border"]};
            background: #FFFFFF;
            margin-bottom: 8px;
        }}
        .dataset-card .dataset-name {{ font-weight: 700; color: {PALETTE["text"]}; font-size: 0.96rem; }}
        .dataset-card .dataset-desc {{ color: {PALETTE["text_muted"]}; font-size: 0.8rem; margin: 2px 0 6px 0; }}
        .dataset-card .dataset-meta {{ color: {PALETTE["text_muted"]}; font-size: 0.78rem; }}

        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 10px; margin: 4px 0 8px 0; }}
        .metric-card {{ background: {PALETTE["bg_card"]}; border: 1px solid {PALETTE["border"]}; border-radius: 12px; padding: 12px 14px; text-align:center; }}
        .metric-card .metric-value {{ font-size: 1.3rem; color: {PALETTE["text"]}; font-weight: 700; line-height: 1.2; }}
        .metric-card .metric-label {{ font-size: 0.76rem; color: {PALETTE["text_muted"]}; font-weight: 500; margin-top: 2px; }}

        .example-row {{
            padding: 8px 12px;
            border-radius: 10px;
            border: 1px solid {PALETTE["border"]};
            background: #FFFFFF;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .example-row.selected {{ border-color: {PALETTE["primary"]}; background: {PALETTE["primary_soft"]}; }}
        .example-id {{ font-weight: 700; color: {PALETTE["text"]}; font-size: 0.85rem; }}
        .dot-row {{ display: inline-flex; gap: 4px; margin-left: 8px; }}
        .dot {{ width: 12px; height: 12px; border-radius: 50%; display: inline-block; }}

        .balance-bar {{ display: flex; height: 10px; border-radius: 6px; overflow: hidden; margin: 6px 0 4px 0; }}
        .balance-pos {{ background: {PALETTE["success"]}; }}
        .balance-neg {{ background: {PALETTE["error"]}; }}
        .balance-caption {{ display: flex; justify-content: space-between; font-size: 0.78rem; color: {PALETTE["text_muted"]}; }}

        .chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 14px 0; }}
        .chip {{ border-radius: 999px; padding: 4px 12px; font-size: 0.8rem; font-weight: 500; }}
        .chip-neutral {{ background: {PALETTE["neutral_soft"]}; color: {PALETTE["text"]}; }}
        .chip-primary {{ background: {PALETTE["primary_soft"]}; color: {PALETTE["primary"]}; }}
        .chip-success {{ background: {PALETTE["success_soft"]}; color: {PALETTE["success"]}; }}
        .chip-error {{ background: {PALETTE["error_soft"]}; color: {PALETTE["error"]}; }}
        .chip b {{ font-weight: 500; opacity: 0.7; margin-right: 4px; }}

        .intro-card {{
            padding: 1.1rem 1.4rem;
            border-radius: 14px;
            background: {PALETTE["primary_soft"]};
            border: 1px solid {PALETTE["border"]};
            margin-bottom: 1.2rem;
            color: {PALETTE["text"]};
            font-size: 0.92rem;
            line-height: 1.5;
        }}
        .intro-card b {{ color: {PALETTE["primary"]}; }}

        div[data-testid="stCodeBlock"],
        div[data-testid="stCode"] {{
            max-height: 480px !important;
            overflow-y: auto !important;
        }}
        div[data-testid="stCodeBlock"] pre,
        div[data-testid="stCode"] pre {{
            max-height: 480px !important;
            overflow-y: auto !important;
        }}

        .rep-card {{
            height: 100%;
            padding: 1.1rem 1.2rem;
            border-radius: 16px;
            border: 1.5px solid {PALETTE["border"]};
            background: #FFFFFF;
        }}
        .rep-card .rep-title {{ font-weight: 700; font-size: 1.0rem; margin-bottom: 4px; }}
        .rep-card .rep-body {{ color: {PALETTE["text_muted"]}; font-size: 0.87rem; line-height: 1.5; margin-bottom: 10px; }}

        /* Row-style tertiary buttons — used for the scrollable dataset
           and example lists: no button chrome, click anywhere on the
           row, plain hover highlight instead. */
        .stButton button[kind="tertiary"] {{
            width: 100%;
            text-align: left !important;
            justify-content: flex-start !important;
            padding: 10px 12px !important;
            border-radius: 10px !important;
            white-space: pre-line !important;
        }}
        .stButton button[kind="tertiary"] p {{
            text-align: left !important;
            white-space: pre-line !important;
        }}
        .stButton button[kind="tertiary"]:hover {{
            background: {PALETTE["bg_card"]} !important;
        }}

        /* --------------------------------------------------------- */
        /* Dark navy sidebar, matching the Experiments page          */
        /* --------------------------------------------------------- */

        section[data-testid="stSidebar"] {{
            background: #0F1B33 !important;
            border-right: 1px solid #22314F;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {{
            height: auto !important;
            min-height: 0 !important;
            margin-bottom: 4px !important;
            padding-top: 6px !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] img,
        section[data-testid="stSidebar"] [data-testid="stLogo"] {{
            height: 76px !important;
            max-height: none !important;
            width: auto !important;
            max-width: 100% !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] {{
            display: none !important;
        }}
        section[data-testid="stSidebar"] > div:first-child {{
            min-height: 100vh !important;
            display: flex !important;
            flex-direction: column !important;
        }}
        [data-testid="stSidebarNav"] {{
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 auto !important;
            min-height: 0 !important;
        }}
        [data-testid="stSidebarNavItems"] {{
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 auto !important;
        }}
        [data-testid="stSidebarNavItems"] li:nth-last-of-type(2) {{
            margin-top: auto !important;
            padding-top: 303px;
            border-top: 1px solid #22314F;
        }}
        section[data-testid="stSidebar"] * {{
            color: #C7D2EC !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {{
            border-radius: 10px;
            margin: 2px 8px 2px 0 !important;
            padding: 8px 8px 8px 4px !important;
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a > span:first-child {{
            margin: 0 !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            flex-shrink: 0 !important;
            width: auto !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a [data-testid="stIconMaterial"] {{
            width: 27px !important;
            height: 27px !important;
            min-width: 27px !important;
            font-size: 27px !important;
            margin: 0 !important;
            padding: 0 !important;
            color: #E4EAFB !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a > span:last-child {{
            font-size: 18px !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] [data-testid="stIconMaterial"] {{
            color: #FFFFFF !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {{
            background: #1B2A4C !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background: #1B2A4C !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] * {{
            color: #FFFFFF !important;
            font-weight: 600;
        }}
        section[data-testid="stSidebar"] hr {{
            border-color: #22314F !important;
        }}
        section[data-testid="stSidebar"] .stButton button {{
            background: {PALETTE["primary"]} !important;
            color: #FFFFFF !important;
            border: none !important;
        }}
        section[data-testid="stSidebar"] input {{
            background: #1B2A4C !important;
            color: #FFFFFF !important;
            border-color: #22314F !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_badge(text: str, color: str, bg: str) -> str:
    return f'<span class="badge" style="color:{color};background:{bg};">{text}</span>'


def render_metric_grid(items: list[tuple[str, str]]) -> None:
    cards = "".join(
        f'<div class="metric-card"><div class="metric-value">{value}</div>'
        f'<div class="metric-label">{label}</div></div>'
        for label, value in items
    )
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)


def render_balance_bar(positive: int, negative: int) -> None:
    total = positive + negative
    pos_pct = round(100 * positive / total) if total else 0
    neg_pct = 100 - pos_pct if total else 0
    st.markdown(
        f'<div class="balance-bar">'
        f'<div class="balance-pos" style="width:{pos_pct}%;"></div>'
        f'<div class="balance-neg" style="width:{neg_pct}%;"></div>'
        f"</div>"
        f'<div class="balance-caption">'
        f"<span>{positive} positive ({pos_pct}%)</span>"
        f"<span>{negative} negative ({neg_pct}%)</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_stats_grid(items: list[dict]) -> None:
    """Same visual as render_metric_grid, but takes {label, value} dicts —
    matches the Dataset Explorer page's own helper exactly."""
    cards = "".join(
        f'<div class="metric-card"><div class="metric-value">{item["value"]}</div>'
        f'<div class="metric-label">{item["label"]}</div></div>'
        for item in items
    )
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)


def render_chips(pairs: list[tuple[str, str]], variant: str = "neutral") -> None:
    chips = "".join(
        f'<span class="chip chip-{variant}"><b>{label}</b>{value}</span>'
        for label, value in pairs
    )
    st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)


def extract_target_predicates(bias_text: str) -> list[str]:
    targets = []
    for pattern in (r"head_pred\(([^)]+)\)", r"target\(([^)]+)\)"):
        for match in re.findall(pattern, bias_text):
            if match not in targets:
                targets.append(match)
    return targets


def count_facts(background_text: str) -> int:
    return sum(1 for line in clean_prolog_lines(background_text) if line.endswith("."))


# ---------------------------------------------------------------------
# Dataset helpers
# ---------------------------------------------------------------------

def get_available_datasets() -> list[str]:
    if not DATASETS_DIRECTORY.is_dir():
        return []
    return sorted(
        directory.name
        for directory in DATASETS_DIRECTORY.iterdir()
        if directory.is_dir()
        and directory.name != "generated"
        and directory.name != "andante"
        and "_part" not in directory.name
        and (directory / "exs.pl").is_file()
        and (directory / "bk.pl").is_file()
        and (directory / "bias.pl").is_file()
    )


def get_available_andante_datasets() -> list[str]:
    """Native, hand-written Andante examples — single .pl files (mode
    declarations + background knowledge + examples all in one), stored
    under datasets/andante/. Unlike Popper datasets, these aren't
    auto-converted from anything; they're used as-is."""
    andante_directory = DATASETS_DIRECTORY / "andante"
    if not andante_directory.is_dir():
        return []
    return sorted(
        file.stem
        for file in andante_directory.glob("*.pl")
    )


def read_text_file(file_path: Path) -> str:
    if not file_path.is_file():
        return ""
    return file_path.read_text(encoding="utf-8", errors="replace")


def clean_prolog_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("%"):
            continue
        lines.append(stripped)
    return lines


def split_examples(examples_text: str) -> tuple[list[str], list[str]]:
    positive_examples, negative_examples = [], []
    for line in clean_prolog_lines(examples_text):
        if line.startswith("pos("):
            positive_examples.append(line)
        elif line.startswith("neg("):
            negative_examples.append(line)
    return positive_examples, negative_examples


def format_dataset_name(dataset_name: str) -> str:
    return dataset_name.replace("_", " ").replace("-", " ").title()


def count_andante_examples(andante_text: str) -> tuple[int, int]:
    """Count positive/negative examples in a native Andante .pl file —
    the lines between :- begin_in_pos./:- end_in_pos. and
    :- begin_in_neg./:- end_in_neg., one fact per line (no pos()/neg()
    wrapper, unlike Popper's exs.pl)."""

    def _count_section(text: str, begin: str, end: str) -> int:
        if begin not in text or end not in text:
            return 0
        body = text.split(begin, 1)[1].split(end, 1)[0]
        return sum(
            1
            for line in body.splitlines()
            if line.strip() and not line.strip().startswith("%")
        )

    positive_count = _count_section(andante_text, ":- begin_in_pos.", ":- end_in_pos.")
    negative_count = _count_section(andante_text, ":- begin_in_neg.", ":- end_in_neg.")
    return positive_count, negative_count


def strip_pos_neg(example_line: str) -> str:
    inner = example_line
    for wrapper in ("pos(", "neg("):
        if inner.startswith(wrapper):
            inner = inner[len(wrapper):]
            if inner.endswith(")."):
                inner = inner[:-2] + "."
            break
    return inner


def example_inner_identifier(example_atom: str) -> str:
    """zendo(10). -> '10' — falls back to the whole atom if there are no parens."""
    start = example_atom.find("(")
    end = example_atom.rfind(")")
    if start == -1 or end == -1 or end <= start:
        return example_atom.rstrip(".")
    return example_atom[start + 1:end].strip()


SIZE_PIXELS = {"small": 16, "medium": 24, "large": 32}


def parse_size_categories(background_text: str) -> dict[str, str]:
    """Zendo bk.pl encodes size as size(piece, V). then small(V)./medium(V)./
    large(V). — this maps each numeric value V to its category, so a piece's
    size can be resolved without inventing anything."""
    categories: dict[str, str] = {}
    for line in clean_prolog_lines(background_text):
        match = re.match(r"^(small|medium|large)\((\w+)\)\.$", line)
        if match:
            categories[match.group(2)] = match.group(1)
    return categories


SHAPE_BY_COLOR = {
    "red": "circle",
    "green": "circle",
    "blue": "square",
}


def build_pieces(local_facts: list[str], size_categories: dict[str, str]) -> list[dict]:
    """Derive each piece's real colour and size category from this example's
    own background facts. The dataset has no "shape" attribute at all, so
    the shape drawn per piece is a fixed, made-up convention (red=circle,
    blue=square, green=triangle) purely to make pieces easier to tell
    apart at a glance — only the colour and size are actual data."""
    piece_ids = []
    for fact in local_facts:
        match = re.match(r"^piece\([^,]+,\s*([\w']+)\)\.$", fact)
        if match:
            piece_ids.append(match.group(1))

    pieces = []
    for piece_id in piece_ids:
        color_name = next(
            (name for name in COLOR_SWATCH if f"{name}({piece_id})." in local_facts),
            None,
        )
        size_value = None
        for fact in local_facts:
            match = re.match(rf"^size\({re.escape(piece_id)},\s*(\w+)\)\.$", fact)
            if match:
                size_value = match.group(1)
                break
        size_category = size_categories.get(size_value, "medium")
        pieces.append(
            {
                "color": COLOR_SWATCH.get(color_name, PALETTE["neutral"]),
                "shape": SHAPE_BY_COLOR.get(color_name, "circle"),
                "size": size_category,
            }
        )
    return pieces


def render_shape(color: str, shape: str, size_px: int, gap: int) -> str:
    if shape == "square":
        return (
            f'<span style="display:inline-block; width:{size_px}px; height:{size_px}px; '
            f'border-radius:4px; background:{color}; margin-right:{gap}px;"></span>'
        )
    if shape == "triangle":
        half = size_px // 2
        return (
            f'<span style="display:inline-block; width:0; height:0; '
            f'border-left:{half}px solid transparent; border-right:{half}px solid transparent; '
            f'border-bottom:{size_px}px solid {color}; margin-right:{gap}px;"></span>'
        )
    return (
        f'<span style="display:inline-block; width:{size_px}px; height:{size_px}px; '
        f'border-radius:50%; background:{color}; margin-right:{gap}px;"></span>'
    )


def render_piece_icons(pieces: list[dict], gap: int = 6) -> str:
    if not pieces:
        return ""
    shapes = "".join(
        render_shape(p["color"], p["shape"], SIZE_PIXELS[p["size"]], gap)
        for p in pieces
    )
    return f'<div style="display:flex; align-items:center;">{shapes}</div>'


def infer_fact_identifier(fact_text: str) -> str | None:
    """Zendo-style per-example tagging: blue(p10_1). -> '10'. Facts without
    such an indexed term are considered shared background knowledge."""
    match = re.search(r"\bp(\d+)_\d+\b", fact_text)
    return match.group(1) if match else None


def dataset_size_label(example_count: int) -> str:
    if example_count < 20:
        return "Small"
    if example_count <= 100:
        return "Medium"
    return "Large"


def count_distinct_constants(background_text: str) -> int:
    tokens: set[str] = set()
    for line in clean_prolog_lines(background_text):
        match = re.match(r"^[a-zA-Z_][\w']*\(([^)]*)\)\.$", line)
        if not match:
            continue
        for token in match.group(1).split(","):
            token = token.strip()
            if token:
                tokens.add(token)
    return len(tokens)


# ---------------------------------------------------------------------
# Popper bias.pl -> Progol-style mode declarations (illustrative
# translation for comparison — the platform's engines run on Popper).
# ---------------------------------------------------------------------

def parse_bias(bias_text: str) -> dict:
    def parse_preds(tag: str) -> list[tuple[str, str]]:
        return re.findall(rf"{tag}\(([\w']+)\s*,\s*(\d+)\)", bias_text)

    def parse_typed(tag: str) -> dict[str, list[str]]:
        result = {}
        for name, args in re.findall(rf"{tag}\(([\w']+)\s*,\s*\(([^)]*)\)\)", bias_text):
            tokens = [token.strip() for token in args.split(",") if token.strip()]
            result[name] = tokens
        return result

    settings = {}
    for key in ("max_clauses", "max_vars", "max_body"):
        match = re.search(rf"{key}\((\d+)\)", bias_text)
        if match:
            settings[key] = match.group(1)

    return {
        "head_preds": parse_preds("head_pred"),
        "body_preds": parse_preds("body_pred"),
        "types": parse_typed("type"),
        "directions": parse_typed("direction"),
        "settings": settings,
    }


def build_mode_line(name: str, arity: str, types: dict, directions: dict, recall: str) -> str:
    arg_types = types.get(name, ["any"] * int(arity))
    arg_dirs = directions.get(name, ["in"] * int(arity))
    parts = []
    for direction, type_name in zip(arg_dirs, arg_types):
        sign = "+" if direction == "in" else ("-" if direction == "out" else "#")
        parts.append(f"{sign}{type_name}")
    return f"modeb({recall}, {name}({', '.join(parts)}))."


def build_progol_modes(parsed: dict) -> list[str]:
    lines = []
    for name, arity in parsed["head_preds"]:
        line = build_mode_line(name, arity, parsed["types"], parsed["directions"], recall="1")
        lines.append(line.replace("modeb(", "modeh(", 1))
    for name, arity in parsed["body_preds"]:
        lines.append(build_mode_line(name, arity, parsed["types"], parsed["directions"], recall="*"))
    return lines


def build_progol_examples(positive_examples: list[str], negative_examples: list[str]) -> list[str]:
    lines = [strip_pos_neg(example) for example in positive_examples]
    lines += [f":- {strip_pos_neg(example)}" for example in negative_examples]
    return lines


# ---------------------------------------------------------------------
# Learned programs (real, stored results — nothing fabricated)
# ---------------------------------------------------------------------

def load_latest_hypotheses() -> list[dict]:
    with get_connection() as connection:
        experiment_rows = connection.execute(
            """
            SELECT id, approach, dataset, completed_at
            FROM experiments
            WHERE status = 'COMPLETED'
            ORDER BY completed_at DESC
            """
        ).fetchall()

        seen_approaches: set[str] = set()
        results = []

        for row in experiment_rows:
            approach = row["approach"]
            if approach in seen_approaches:
                continue

            if approach == "consensus":
                result_row = connection.execute(
                    "SELECT hypotheses FROM consensus_results WHERE experiment_id = ?",
                    (row["id"],),
                ).fetchone()
                if not result_row or not result_row["hypotheses"]:
                    continue
                try:
                    hypotheses = json.loads(result_row["hypotheses"])
                except (TypeError, ValueError):
                    hypotheses = []
                if not hypotheses:
                    continue
            else:
                result_row = connection.execute(
                    "SELECT solution FROM server_results WHERE experiment_id = ?",
                    (row["id"],),
                ).fetchone()
                if not result_row or not result_row["solution"]:
                    continue
                hypotheses = [result_row["solution"]]

            seen_approaches.add(approach)
            results.append(
                {
                    "approach": approach,
                    "experiment_id": row["id"],
                    "dataset": row["dataset"],
                    "completed_at": row["completed_at"],
                    "hypotheses": hypotheses,
                }
            )

        return results


# =======================================================================
# Page body
# =======================================================================

inject_style()

st.markdown('<div class="breadcrumb">Home &gt; Inductive Logic Programming</div>', unsafe_allow_html=True)

header_left, header_right = st.columns([1.5, 2])

with header_left:
    st.title("Inductive Logic Programming")
    st.markdown(
        f'<div style="font-size:1.25rem; color:{PALETTE["text_muted"]}; margin-top:-6px;">'
        "Learn logical rules from examples.</div>",
        unsafe_allow_html=True,
    )

with header_right:
    ICON_LIGHTBULB = (
        f'<svg viewBox="0 0 24 24" width="22" height="22" fill="none" '
        f'stroke="{PALETTE["text"]}" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round">'
        '<path d="M9 18h6"/><path d="M10 21h4"/>'
        '<path d="M12 3a6 6 0 0 0-3.6 10.8c.6.45 1.1 1.15 1.2 1.95V16h4.8v-.25c.1-.8.6-1.5 1.2-1.95A6 6 0 0 0 12 3z"/>'
        "</svg>"
    )
    st.markdown(
        '<div class="ilp-banner">'
        f'<div class="banner-icon">{ICON_LIGHTBULB}</div>'
        '<div class="banner-body">ILP sits at the <b>intersection of Logic '
        "Programming and Machine Learning</b>: instead of fitting weights, "
        "it induces symbolic rules a human can read and verify. This is "
        "what makes it a candidate for <b>Ultra-Strong Machine Learning</b> "
        "(Michie, 1988), learning that doesn't just predict well, but "
        "produces knowledge a human can be taught, to perform the task "
        "better themselves.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

st.write("")

overview_tab, examples_tab, try_learn_tab, custom_ilp_tab = st.tabs(
    ["Overview", "Examples", "Try & Learn", "Custom ILP"]
)


# =======================================================================
# OVERVIEW TAB — core concepts: logic programming, the ILP problem,
# Prolog, ASP, Progol, and where this platform fits among ILP systems.
# =======================================================================

with overview_tab:
    st.markdown('<div class="section-title">What is logic programming?</div>', unsafe_allow_html=True)
    st.markdown(
        "**Logic programming** is a programming paradigm where a program "
        "isn't a sequence of instructions but a set of logical statements, "
        "facts and rules and a query is answered by *proving* it from "
        "those statements, not by executing steps. Prolog is the classic "
        "language for it; it's built from exactly three ingredients:"
    )

    lp_col_1, lp_col_2, lp_col_3 = st.columns(3)
    with lp_col_1:
        st.markdown(
            "**Facts:** atomic statements taken as true, e.g. `red(b3).` "
            "or `piece(s1, b3).`, no logic, just data."
        )
    with lp_col_2:
        st.markdown(
            "**Rules:** statements of the form `head :- body.`, e.g. "
            "`zendo(S) :- piece(S,P), red(P).`"
        )
    with lp_col_3:
        st.markdown(
            "**Queries:**  a logic program answers questions by "
            "resolution: searching for a chain of facts and rules "
            "that proves (or disproves) a goal."
        )

    st.info(
        "**Where the \"Machine Learning\" in ILP actually comes from**, "
        "on its own, logic programming isn't learning: a Prolog program "
        "only proves what it's already been told. ILP turns it into ML by "
        "flipping the direction: instead of writing the rules by hand, it "
        "starts from **facts** (background knowledge) and a set of "
        "**observed examples**, and *searches for* a rule general enough "
        "to explain them, generalizing from specific observations to a "
        "rule that also covers unseen cases. That's the same inductive "
        "principle as statistical ML (learn a general pattern from data); "
        "ILP just represents what it learns as symbolic logic instead of "
        "numeric weights.",
        icon=":material/psychology:",
    )

    st.divider()

    st.markdown('<div class="section-title">The ILP learning problem</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <style>
        div[class*="st-key-ilp_problem_box"] {{
            background: {PALETTE["bg_card"]};
        }}
        div[class*="st-key-ilp_problem_box"] [data-testid="stMarkdownContainer"] {{
            margin-bottom: 0 !important;
        }}
        div[class*="st-key-ilp_problem_box"] [data-testid="stElementContainer"] {{
            margin-bottom: 0 !important;
        }}
        div[class*="st-key-ilp_problem_box"] .katex-display {{
            margin: 0.4rem 0 0 0 !important;
        }}
        div[class*="st-key-ilp_problem_box"] [data-testid="stVerticalBlock"] {{
            gap: 0 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="ilp_problem_box", border=True):
        st.markdown(
            "**ILP Problem Setting**  ILP combines logic programming and "
            "machine learning to derive interpretable rules from "
            "structured data. Given background knowledge $B_k$, a set of "
            "positive examples $E^+$, and a set of negative examples "
            "$E^-$, the task is to induce a hypothesis $H$ (a logic "
            "program) such that:"
        )
        st.latex(
            r"\forall e^+ \in E^+ : B_k \cup H \vdash e^+"
            r"\qquad \text{and} \qquad"
            r"\forall e^- \in E^- : B_k \cup H \nvdash e^-."
        )

    st.markdown(
        "Every approach on this platform searches for exactly such an "
        "*H* — they differ only in how that search is distributed across "
        "clients.\n\n"
        "📄 [*Inductive Logic Programming* — Muggleton (1991), "
        "*New Generation Computing*, 8:295–318](https://www.doc.ic.ac.uk/~shm/Papers/ilp.pdf)"
    )

    st.divider()

    st.markdown('<div class="section-title">The building blocks: Prolog, ASP, and ILP systems</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">ILP does not invent its own logic — it reuses existing logic-programming languages to represent and search for hypotheses</div>',
        unsafe_allow_html=True,
    )

    block_col_1, block_col_2, block_col_3 = st.columns(3)
    with block_col_1:
        st.markdown(
            f'<div class="rep-card" style="border-color:{PALETTE["popper"]}40;">'
            + render_badge("Language", PALETTE["popper"], PALETTE["popper_soft"])
            + '<div class="rep-title" style="margin-top:10px;">Prolog</div>'
            + "<div class=\"rep-body\">A logic-programming language built "
            "around facts, rules and queries answered by resolution. "
            "Hypotheses learned by this platform — and by most ILP systems "
            "— are Prolog programs: small sets of Horn clauses like "
            "<code>head :- body.</code></div>"
            "</div>",
            unsafe_allow_html=True,
        )
    with block_col_2:
        st.markdown(
            f'<div class="rep-card" style="border-color:{PALETTE["primary"]}40;">'
            + render_badge("Solver", PALETTE["primary"], PALETTE["primary_soft"])
            + '<div class="rep-title" style="margin-top:10px;">ASP (Answer Set Programming)</div>'
            + "<div class=\"rep-body\">A declarative paradigm for solving "
            "combinatorial search problems: you describe the constraints, "
            "and a solver enumerates the models that satisfy them. Popper "
            "uses an ASP solver (Clingo) under the hood to ground and "
            "search the space of candidate hypotheses efficiently.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    with block_col_3:
        st.markdown(
            f'<div class="rep-card" style="border-color:{PALETTE["progol"]}40;">'
            + render_badge("ILP system", PALETTE["progol"], PALETTE["progol_soft"])
            + '<div class="rep-title" style="margin-top:10px;">Progol</div>'
            + "<div class=\"rep-body\">One of the classic ILP systems, "
            "built on <b>inverse entailment</b>: it builds the most "
            "specific clause that entails an example, then searches a "
            "refinement graph beneath it, guided by mode declarations "
            "(<code>modeh</code>/<code>modeb</code>).</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown(
        "There are many other ILP systems beyond Progol, Aleph, FOIL, "
        "TILDE, Metagol, ILASP, among others,  each with its own search "
        "strategy and bias language. This platform is built on "
        "**Popper**, a more recent system that reformulates ILP search as "
        "constraint solving over ASP, and every dataset here is described "
        "in Popper's own representation (`exs.pl` / `bk.pl` / `bias.pl`). "
        "The Progol view below is auto-translated for comparison, since "
        "Progol-style mode declarations remain the reference most "
        "ILP literature is written against."
    )

    st.divider()

    st.markdown('<div class="section-title">Two ways to write a language bias</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">Without restrictions the space of candidate programs is infinite — a bias tells the learner what a hypothesis is even allowed to look like. This platform runs on Popper; the Progol view below is auto-translated from each dataset\'s bias.pl for comparison.</div>',
        unsafe_allow_html=True,
    )

    rep_col_1, rep_col_2 = st.columns(2)
    with rep_col_1:
        st.markdown(
            f'<div class="rep-card" style="border-color:{PALETTE["progol"]}40;">'
            + render_badge("Progol / Aleph", PALETTE["progol"], PALETTE["progol_soft"])
            + '<div class="rep-title" style="margin-top:10px;">Mode declarations</div>'
            + "<div class=\"rep-body\">Each predicate gets a <code>modeh</code> "
            "(head) or <code>modeb</code> (body) declaration. Arguments are "
            "annotated <code>+</code> (input), <code>-</code> (output) or "
            "<code>#</code> (constant), followed by their type.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.code(
            "modeh(1, zendo(+state)).\n"
            "modeb(*, piece(+state, -piece)).\n"
            "modeb(*, red(+piece)).",
            language="prolog",
        )
    with rep_col_2:
        st.markdown(
            f'<div class="rep-card" style="border-color:{PALETTE["popper"]}40;">'
            + render_badge("Popper", PALETTE["popper"], PALETTE["popper_soft"])
            + '<div class="rep-title" style="margin-top:10px;">Declarative bias (bias.pl)</div>'
            + "<div class=\"rep-body\"><code>head_pred/2</code> and "
            "<code>body_pred/2</code> declare allowed predicates, "
            "<code>type/2</code> and <code>direction/2</code> play the role "
            "of Progol's <code>+/-/#</code>, and <code>max_vars</code> / "
            "<code>max_body</code> bound the hypothesis shape.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.code(
            "head_pred(zendo,1).\n"
            "body_pred(piece,2).\n"
            "type(piece,(state,piece)).\n"
            "direction(piece,(in,out)).",
            language="prolog",
        )

    st.write("")

    utility_dataset = st.selectbox(
        "Translate a dataset's bias",
        options=get_available_datasets(),
        format_func=format_dataset_name,
        key="utility_dataset",
    )

    utility_directory = DATASETS_DIRECTORY / utility_dataset
    utility_bias_text = read_text_file(utility_directory / "bias.pl")
    utility_examples_text = read_text_file(utility_directory / "exs.pl")
    utility_positive, utility_negative = split_examples(utility_examples_text)
    utility_parsed = parse_bias(utility_bias_text)

    popper_col, progol_col = st.columns(2)
    with popper_col:
        st.markdown("**Popper — bias.pl**")
        st.code(utility_bias_text or "(empty)", language="prolog")
    with progol_col:
        st.markdown("**Progol-style — mode declarations**")
        st.code("\n".join(build_progol_modes(utility_parsed)) or "(none)", language="prolog")
        with st.expander("Examples (Progol/Aleph convention)"):
            st.code(
                "\n".join(build_progol_examples(utility_positive, utility_negative)) or "(none)",
                language="prolog",
            )


# =======================================================================
# EXAMPLES TAB — the Dataset Explorer page (2_Datasets.py), as-is
# =======================================================================

with examples_tab:
    explorer_datasets = get_available_datasets()

    if not explorer_datasets:
        st.error("No valid dataset was found in the datasets directory.")
    else:
        picker_col, main_col = st.columns([1, 3])

        with picker_col:
            st.markdown('<div class="section-title">Datasets</div>', unsafe_allow_html=True)

            explorer_selected_dataset = st.radio(
                "Dataset",
                options=explorer_datasets,
                format_func=format_dataset_name,
                label_visibility="collapsed",
                key="explorer_dataset_radio",
            )

            st.divider()

            explorer_directory = DATASETS_DIRECTORY / explorer_selected_dataset

            explorer_examples_text = read_text_file(explorer_directory / "exs.pl")
            explorer_background_text = read_text_file(explorer_directory / "bk.pl")
            explorer_bias_text = read_text_file(explorer_directory / "bias.pl")

            explorer_positive, explorer_negative = split_examples(explorer_examples_text)
            explorer_targets = extract_target_predicates(explorer_bias_text)
            explorer_fact_count = count_facts(explorer_background_text)
            explorer_line_count = len(explorer_background_text.splitlines())

            st.markdown('<div class="section-title">At a glance</div>', unsafe_allow_html=True)

            render_stats_grid(
                [
                    {"label": "Examples", "value": len(explorer_positive) + len(explorer_negative)},
                    {"label": "Positive", "value": len(explorer_positive)},
                    {"label": "Negative", "value": len(explorer_negative)},
                    {"label": "Background facts", "value": explorer_fact_count},
                ]
            )

            render_balance_bar(len(explorer_positive), len(explorer_negative))

            if explorer_targets:
                st.markdown(
                    '<div class="section-title" style="margin-top:14px;">Target predicate(s)</div>',
                    unsafe_allow_html=True,
                )
                render_chips([(t, "") for t in explorer_targets], variant="primary")

        with main_col:
            st.markdown(
                '<div class="intro-card">A dataset is a set of Prolog files: '
                "<b>positive / negative examples</b> define the concept to learn, "
                "<b>background knowledge</b> gives the learner facts and relations "
                "to reason over, and the <b>language bias</b> restricts the shape "
                "of hypotheses Popper is allowed to construct.</div>",
                unsafe_allow_html=True,
            )

            explorer_header_left, explorer_header_right = st.columns([4, 2])

            with explorer_header_left:
                st.markdown(
                    f'<div class="section-title" style="font-size:1.2rem;">{format_dataset_name(explorer_selected_dataset)}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="section-caption">{explorer_directory}</div>',
                    unsafe_allow_html=True,
                )

            with explorer_header_right:
                render_chips(
                    [
                        ("Examples", str(len(explorer_positive) + len(explorer_negative))),
                        ("Facts", str(explorer_fact_count)),
                    ],
                    variant="neutral",
                )

            explorer_examples_tab, explorer_background_tab, explorer_bias_tab = st.tabs(
                ["Examples", "Background knowledge", "Language bias"]
            )

            # --- Examples tab -------------------------------------------

            with explorer_examples_tab:
                code_column, stats_column = st.columns([3, 1])

                with stats_column:
                    with st.container(border=True):
                        st.markdown('<div class="section-title">Counts</div>', unsafe_allow_html=True)
                        render_stats_grid(
                            [
                                {"label": "Positive", "value": len(explorer_positive)},
                                {"label": "Negative", "value": len(explorer_negative)},
                                {"label": "Total", "value": len(explorer_positive) + len(explorer_negative)},
                            ]
                        )
                        render_balance_bar(len(explorer_positive), len(explorer_negative))
                        st.caption("Source: `exs.pl`")

                with code_column:
                    positive_view, negative_view = st.tabs(
                        [f"Positive ({len(explorer_positive)})", f"Negative ({len(explorer_negative)})"]
                    )

                    with positive_view:
                        st.caption("Expected to be entailed by the learned hypothesis.")
                        if explorer_positive:
                            with st.container(height=420, border=True):
                                st.code("\n".join(explorer_positive), language="prolog", line_numbers=True)
                        else:
                            st.warning("No positive example was found in exs.pl.")

                    with negative_view:
                        st.caption("Must NOT be entailed by the learned hypothesis.")
                        if explorer_negative:
                            with st.container(height=420, border=True):
                                st.code("\n".join(explorer_negative), language="prolog", line_numbers=True)
                        else:
                            st.warning("No negative example was found in exs.pl.")

                    with st.expander("View the complete exs.pl file"):
                        with st.container(height=420, border=False):
                            st.code(explorer_examples_text, language="prolog", line_numbers=True)

            # --- Background knowledge tab --------------------------------

            with explorer_background_tab:
                code_column, stats_column = st.columns([3, 1])

                with stats_column:
                    with st.container(border=True):
                        st.markdown('<div class="section-title">Counts</div>', unsafe_allow_html=True)
                        render_stats_grid(
                            [
                                {"label": "Facts", "value": explorer_fact_count},
                                {"label": "Lines", "value": explorer_line_count},
                            ]
                        )
                        st.caption("Source: `bk.pl`")

                with code_column:
                    st.caption(
                        "Facts and, depending on the dataset, reusable rules that "
                        "describe the domain — objects, relations, attributes."
                    )

                    explorer_background_lines = explorer_background_text.splitlines()

                    filter_col, size_col, page_col = st.columns([2, 1, 1])

                    with filter_col:
                        explorer_search_term = st.text_input(
                            "Search",
                            placeholder="Filter lines (e.g. a predicate name)…",
                            key=f"bk_search_{explorer_selected_dataset}",
                        )

                    with size_col:
                        explorer_preview_size = st.selectbox(
                            "Lines per page",
                            options=[50, 100, 200, 500],
                            index=1,
                            key=f"bk_page_size_{explorer_selected_dataset}",
                        )

                    explorer_display_lines = (
                        [line for line in explorer_background_lines if explorer_search_term.lower() in line.lower()]
                        if explorer_search_term
                        else explorer_background_lines
                    )
                    explorer_number_of_lines = len(explorer_display_lines)
                    explorer_number_of_pages = max(
                        1, (explorer_number_of_lines + explorer_preview_size - 1) // explorer_preview_size
                    )

                    with page_col:
                        explorer_selected_page = st.number_input(
                            "Page",
                            min_value=1,
                            max_value=explorer_number_of_pages,
                            value=1,
                            step=1,
                            key=f"bk_page_{explorer_selected_dataset}",
                        )

                    explorer_start_index = (int(explorer_selected_page) - 1) * explorer_preview_size
                    explorer_end_index = min(explorer_start_index + explorer_preview_size, explorer_number_of_lines)
                    explorer_visible_background = "\n".join(
                        explorer_display_lines[explorer_start_index:explorer_end_index]
                    )

                    st.caption(
                        f"Showing lines {explorer_start_index + 1}–{explorer_end_index} of {explorer_number_of_lines}"
                        + (f" (filtered from {explorer_line_count})" if explorer_search_term else "")
                    )

                    with st.container(height=420, border=True):
                        st.code(explorer_visible_background or "—", language="prolog", line_numbers=True)

            # --- Bias tab --------------------------------------------------

            with explorer_bias_tab:
                code_column, stats_column = st.columns([3, 1])

                with stats_column:
                    with st.container(border=True):
                        st.markdown('<div class="section-title">Target predicate(s)</div>', unsafe_allow_html=True)
                        if explorer_targets:
                            render_chips([(t, "") for t in explorer_targets], variant="primary")
                        else:
                            st.caption("None detected.")
                        st.caption("Source: `bias.pl`")

                with code_column:
                    st.caption(
                        "Predicates and structural limits (variables, clauses, body "
                        "literals) that Popper may use while building hypotheses."
                    )
                    with st.container(height=420, border=True):
                        st.code(explorer_bias_text or "—", language="prolog", line_numbers=True)


# =======================================================================
# TRY & LEARN TAB — pick a system + dataset, preview a run (demo)
# =======================================================================

with try_learn_tab:
    st.markdown('<div class="section-title">Try a learning run</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">Pick an ILP system and a dataset, then run it — both systems run for real, right here</div>',
        unsafe_allow_html=True,
    )

    st.write("")

    setup_col, result_col = st.columns([1, 1.4], gap="large")

    with setup_col:
        st.markdown("**1. Choose an ILP system**")
        tl_system = st.radio(
            "ILP system",
            options=["Popper", "Andante"],
            horizontal=True,
            label_visibility="collapsed",
            key="try_learn_system",
        )
        if tl_system == "Popper":
            st.caption("Constraint-driven search over ASP, guided by `bias.pl`. Runs live here as a single, non-federated (**centralized**) Popper 1.1.0 job — the same engine behind every approach on this platform, without the federation layer.")
        else:
            st.caption("Progol-style inverse-entailment search guided by mode declarations. Runs live here via Andante — the same local learner already used by Learning by Consensus.")

        st.write("")
        st.markdown("**2. Choose a dataset**")
        # Popper datasets (bias.pl/bk.pl/exs.pl directories) and native
        # Andante examples (single .pl files under datasets/andante/)
        # are two separate pools — Andante here always uses its own
        # hand-written file, never an auto-converted Popper dataset.
        tl_datasets = (
            get_available_andante_datasets()
            if tl_system == "Andante"
            else get_available_datasets()
        )
        tl_dataset = st.selectbox(
            "Dataset",
            options=tl_datasets,
            format_func=format_dataset_name,
            label_visibility="collapsed",
            key="try_learn_dataset",
        )

        if tl_system == "Andante":
            tl_andante_file = DATASETS_DIRECTORY / "andante" / f"{tl_dataset}.pl"
            tl_positive_count, tl_negative_count = count_andante_examples(read_text_file(tl_andante_file))
        else:
            tl_directory = DATASETS_DIRECTORY / tl_dataset
            tl_examples_text = read_text_file(tl_directory / "exs.pl")
            tl_positive, tl_negative = split_examples(tl_examples_text)
            tl_positive_count, tl_negative_count = len(tl_positive), len(tl_negative)
        st.caption(f"{tl_positive_count + tl_negative_count} examples · {tl_positive_count} positive · {tl_negative_count} negative")

        st.write("")
        run_clicked = st.button(
            f"▶ Run {tl_system}",
            type="primary",
            use_container_width=True,
            key="try_learn_run",
            disabled=st.session_state.get("try_learn_running", False),
        )

        stored_result = st.session_state.get("try_learn_result")
        if stored_result and (stored_result["system"] != tl_system or stored_result["dataset"] != tl_dataset):
            st.caption("⚠️ Settings changed since the last run — run again to refresh the result.")

    # -------------------------------------------------------------
    # Running state: step-by-step status, then persist the result to
    # session_state so it survives reruns (e.g. tweaking a widget)
    # instead of disappearing the moment `run_clicked` goes stale.
    # -------------------------------------------------------------

    if run_clicked:
        st.session_state["try_learn_running"] = True
        with result_col:
            st.markdown("**3. Result**")

            # -------------------------------------------------------
            # REAL run — a centralized (non-federated) job, executed via
            # ExperimentLauncher. Popper uses popper-core 1.1.0; Andante
            # uses the same local learner Learning by Consensus already
            # relies on (engines.consensus.learners.andante). Both are
            # dispatched by core/launcher.py::_run_centralized based on
            # config.learner.
            # -------------------------------------------------------
            from core.launcher import ExperimentLauncher
            from core.experiment import ExperimentConfig

            tl_learner = "andante" if tl_system == "Andante" else "popper"
            run_error: str | None = None
            experiment_id: int | None = None

            with st.status(f"Running {tl_system} on `{format_dataset_name(tl_dataset)}`…", expanded=True) as status:
                st.write(f"Loading `{tl_dataset}` — {tl_positive_count} positive, {tl_negative_count} negative examples")
                if tl_learner == "andante":
                    st.write("Launching a centralized Andante run on this native example (no federation, single process)…")
                else:
                    st.write("Launching a centralized Popper 1.1.0 run (no federation, single process)…")
                try:
                    tl_config = ExperimentConfig(
                        approach="centralized",
                        dataset=tl_dataset,
                        number_of_clients=1,
                        partition_strategy="iid",
                        learner=tl_learner,
                        # Same default timeout (600s) as every other
                        # approach on this platform.
                    )
                    experiment_id = ExperimentLauncher().run(tl_config)
                    status.update(label="Run complete", state="complete", expanded=False)
                except Exception as exc:  # noqa: BLE001 — surface any solver error to the user
                    run_error = str(exc)
                    status.update(label="Run failed", state="error", expanded=True)

            if run_error:
                st.session_state["try_learn_result"] = {
                    "system": tl_system,
                    "dataset": tl_dataset,
                    "error": run_error,
                }
            else:
                with get_connection() as _tl_conn:
                    _tl_row = _tl_conn.execute(
                        """
                        SELECT solution, solution_found, total_time_seconds, number_of_programs,
                               tp, fn, tn, fp
                        FROM server_results
                        WHERE experiment_id = ?
                        """,
                        (experiment_id,),
                    ).fetchone()
                server_result = dict(_tl_row) if _tl_row else {}
                hypothesis = server_result.get("solution")

                # tp/fn/tn/fp/duration breakdown aren't stored in the
                # DB (only what every approach shares is) — the full
                # run JSON on disk has the rest, written by
                # engines.centralized.runner / andante_runner.
                run_json_path = (
                    PROJECT_ROOT
                    / "artifacts"
                    / f"experiment_{experiment_id}"
                    / "server_result.json"
                )
                run_metrics: dict = {}
                if run_json_path.is_file():
                    try:
                        run_metrics = json.loads(run_json_path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        run_metrics = {}

                st.session_state["try_learn_result"] = {
                    "system": tl_system,
                    "dataset": tl_dataset,
                    "learner": tl_learner,
                    "hypotheses": [hypothesis] if hypothesis else [],
                    "solution_found": bool(server_result.get("solution_found")),
                    "elapsed": float(server_result.get("total_time_seconds") or 0.0),
                    "number_of_programs": server_result.get("number_of_programs"),
                    "tp": server_result.get("tp"),
                    "fn": server_result.get("fn"),
                    "tn": server_result.get("tn"),
                    "fp": server_result.get("fp"),
                    "accuracy": run_metrics.get("accuracy"),
                    "precision": run_metrics.get("precision"),
                    "recall": run_metrics.get("recall"),
                    "f1": run_metrics.get("f1"),
                    "duration_summary": run_metrics.get("duration_summary") or [],
                    "experiment_id": experiment_id,
                    "real": True,
                }

        st.session_state["try_learn_running"] = False
        st.rerun()

    with result_col:
        if not run_clicked:
            st.markdown("**3. Result**")
            stored_result = st.session_state.get("try_learn_result")

            if not stored_result:
                with st.container(border=True):
                    st.caption("Configure a system and dataset, then run to see the result here.")
            elif stored_result.get("error"):
                with st.container(border=True):
                    st.error(f"The run failed: {stored_result['error']}")
                    if stored_result.get("system") == "Andante":
                        st.caption(
                            "This usually means Andante isn't installed in "
                            "this environment yet (`pip install -e "
                            "symbolic/andante`)."
                        )
                    else:
                        st.caption(
                            "This usually means Popper's dependencies (clingo, "
                            "pyswip + SWI-Prolog) aren't installed in this "
                            "environment yet."
                        )
            else:
                is_stale = (
                    stored_result["system"] != tl_system
                    or stored_result["dataset"] != tl_dataset
                )
                with st.container(border=True):
                    header_col, reset_col = st.columns([3, 1])
                    with header_col:
                        _tl_result_system = stored_result.get("system", "Popper")
                        _tl_result_count_label = (
                            f"({stored_result.get('number_of_programs') or 0} programs tested)"
                            if _tl_result_system == "Popper"
                            else f"({stored_result.get('number_of_programs') or 0} clause(s) learned)"
                        )
                        if stored_result["hypotheses"]:
                            st.success(
                                f"**Real run** — {_tl_result_system} on `{stored_result['dataset']}` "
                                f"found a solution in {stored_result['elapsed']:.1f}s "
                                f"{_tl_result_count_label}"
                            )
                        else:
                            st.warning(
                                f"**Real run** — {_tl_result_system} on `{stored_result['dataset']}` "
                                f"didn't find a complete solution within the time limit "
                                f"({stored_result['elapsed']:.1f}s)"
                            )
                    with reset_col:
                        if st.button("↺ Clear", use_container_width=True, key="try_learn_clear"):
                            st.session_state["try_learn_result"] = None
                            st.rerun()

                    if is_stale:
                        st.warning("This result is for a different configuration than the one selected above — run again to refresh it.")

                    if stored_result["hypotheses"]:
                        for hypothesis in stored_result["hypotheses"]:
                            st.code(hypothesis, language="prolog")
                    elif stored_result.get("real"):
                        st.caption("No hypothesis to show — try a longer search time or a smaller dataset.")

                    # ---------------------------------------------------
                    # Metrics — the same ones Popper itself reports via
                    # stats.log_final_result() / stats.show(): the
                    # confusion matrix, derived accuracy/precision/
                    # recall/F1, and the per-stage timing breakdown.
                    # ---------------------------------------------------
                    if stored_result.get("real") and stored_result.get("accuracy") is not None:
                        st.write("")
                        st.markdown("**Metrics**")

                        metric_cols = st.columns(4)
                        metric_cols[0].metric("Accuracy", f"{stored_result['accuracy']:.0%}")
                        metric_cols[1].metric("Precision", f"{stored_result['precision']:.0%}")
                        metric_cols[2].metric("Recall", f"{stored_result['recall']:.0%}")
                        metric_cols[3].metric("F1", f"{stored_result['f1']:.0%}")

                        conf_cols = st.columns(4)
                        conf_cols[0].metric("TP", stored_result.get("tp") or 0)
                        conf_cols[1].metric("FN", stored_result.get("fn") or 0)
                        conf_cols[2].metric("TN", stored_result.get("tn") or 0)
                        conf_cols[3].metric("FP", stored_result.get("fp") or 0)

                        if stored_result.get("duration_summary"):
                            with st.expander("Time breakdown by stage (like `popper --stats`)"):
                                duration_df = pd.DataFrame(stored_result["duration_summary"])
                                duration_df = duration_df.rename(
                                    columns={
                                        "operation": "Stage",
                                        "called": "Called",
                                        "total": "Total (s)",
                                        "mean": "Mean (s)",
                                        "maximum": "Max (s)",
                                    }
                                )
                                st.dataframe(
                                    duration_df.style.format(
                                        {"Total (s)": "{:.3f}", "Mean (s)": "{:.3f}", "Max (s)": "{:.3f}"}
                                    ),
                                    use_container_width=True,
                                    hide_index=True,
                                )

                    if stored_result.get("real") and stored_result.get("experiment_id"):
                        st.caption(
                            f"Saved as experiment #{stored_result['experiment_id']} "
                            "— also visible in Analytics."
                        )


# =======================================================================
# CUSTOM ILP TAB — upload a CSV/Excel file, convert rows to Prolog facts
# (real conversion), preview a bias, and preview the learning step (demo)
# =======================================================================

with custom_ilp_tab:
    from core.tabular_to_ilp import (
        build_andante_dataset,
        build_conversion_plan,
        build_popper_dataset,
        parse_background_text,
        sanitize_identifier,
    )

    st.markdown('<div class="section-title">Bring your own data</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">Upload a table — one row per sample (e.g. a patient), one column per feature (e.g. a symptom) — and turn it into a real Popper or Andante dataset</div>',
        unsafe_allow_html=True,
    )

    custom_file = st.file_uploader(
        "Upload a CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        key="custom_ilp_upload",
    )

    if custom_file is None:
        st.info(
            "Upload a `.csv` or `.xlsx` file to get started — e.g. one row per patient, "
            "one column per symptom, and one column with the outcome you want to learn "
            "(a complication, a diagnosis, …)."
        )

        # -------------------------------------------------------------
        # Pre-upload guidance chat — for someone who hasn't prepared a
        # file yet and doesn't know what format to use. Kept separate
        # from the post-upload "Ask the AI about this data" chat below
        # (different session_state key, different context: there's no
        # dataset yet, just the tool's own format requirements) and only
        # shown while no file has been uploaded, so it gets out of the
        # way once the real per-dataset chat becomes relevant.
        # -------------------------------------------------------------
        try:
            _custom_gemini_key_preupload = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:  # noqa: BLE001 — no secrets.toml at all, e.g. fresh install
            _custom_gemini_key_preupload = ""

        with st.expander("💬 Not sure what to upload? Ask the AI", expanded=False):
            if not _custom_gemini_key_preupload:
                st.caption(
                    "Add a free `GEMINI_API_KEY` (aistudio.google.com/apikey) to "
                    "`.streamlit/secrets.toml` to enable this."
                )
            else:
                _preupload_chat_key = "custom_ilp_preupload_chat_history"
                if _preupload_chat_key not in st.session_state:
                    st.session_state[_preupload_chat_key] = []

                for msg in st.session_state[_preupload_chat_key]:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

                _preupload_chat_input = st.chat_input(
                    "e.g. \"I want to predict complications from patient symptoms, what should my file look like?\"",
                    key="custom_ilp_preupload_chat_input",
                )
                if _preupload_chat_input:
                    st.session_state[_preupload_chat_key].append(
                        {"role": "user", "content": _preupload_chat_input}
                    )
                    with st.chat_message("user"):
                        st.markdown(_preupload_chat_input)

                    from core.llm_background import chat_reply

                    with st.chat_message("assistant"):
                        try:
                            with st.spinner("Thinking…"):
                                _preupload_context = (
                                    "The user has NOT uploaded a file yet. This tool (Custom ILP, "
                                    "on the FILP platform) turns a table into an inductive logic "
                                    "programming (ILP) dataset for Popper or Andante. Format rules "
                                    "to explain when relevant:\n"
                                    "- One row per sample (e.g. one patient), one column per feature "
                                    "(e.g. a symptom).\n"
                                    "- A boolean-like column (yes/no, oui/non, true/false, 1/0) "
                                    "becomes a unary predicate, e.g. fever(p3).\n"
                                    "- A continuous numeric column (many distinct values) gets "
                                    "automatically binarized around its median into a predicate "
                                    "like high_age(p3) — the user doesn't need to do this "
                                    "themselves.\n"
                                    "- One column must be picked as the target/label to predict "
                                    "(e.g. a diagnosis or outcome), with one or more of its values "
                                    "marked as \"positive\".\n"
                                    "- An optional free-text box lets the user add domain rules "
                                    "like \"if fever and cough then flu\".\n"
                                    "Help the user figure out which columns to include and how to "
                                    "name/format them for their specific use case. Be concise and "
                                    "concrete, answer in the same language the user writes in."
                                )
                                _preupload_reply = chat_reply(
                                    st.session_state[_preupload_chat_key],
                                    context=_preupload_context,
                                    api_key=_custom_gemini_key_preupload,
                                )
                            st.markdown(_preupload_reply)
                            st.session_state[_preupload_chat_key].append(
                                {"role": "assistant", "content": _preupload_reply}
                            )
                        except Exception as exc:  # noqa: BLE001 — surface API errors inline, don't crash
                            st.error(f"Chat failed: {exc}")
    else:
        try:
            if custom_file.name.lower().endswith(".csv"):
                custom_df = pd.read_csv(custom_file)
            else:
                custom_df = pd.read_excel(custom_file)
        except Exception as exc:  # noqa: BLE001 — surface any parse error to the user
            custom_df = None
            st.error(f"Couldn't read this file: {exc}")

        if custom_df is not None:
            st.write("")
            st.markdown(f"**Preview** — {len(custom_df)} rows · {len(custom_df.columns)} columns")
            st.dataframe(custom_df.head(20), use_container_width=True)

            st.write("")
            st.markdown("**1. Choose what to learn**")
            safe_columns = [str(c) for c in custom_df.columns]

            target_col1, target_col2 = st.columns([1, 1])
            with target_col1:
                custom_target_column = st.selectbox(
                    "Target column (what you want to predict)",
                    options=safe_columns,
                    index=len(safe_columns) - 1,
                    key="custom_ilp_target_column",
                )
            with target_col2:
                target_unique_values = sorted(
                    {str(v) for v in custom_df[custom_target_column].dropna().unique()}
                )
                custom_positive_values = st.multiselect(
                    "Positive value(s) — everything else becomes negative",
                    options=target_unique_values,
                    default=target_unique_values[:1],
                    key="custom_ilp_positive_values",
                )

            custom_feature_columns = st.multiselect(
                "Feature columns to use (each becomes its own predicate)",
                options=[c for c in safe_columns if c != custom_target_column],
                default=[c for c in safe_columns if c != custom_target_column],
                key="custom_ilp_feature_columns",
            )

            st.write("")
            st.markdown("**2. Add domain knowledge (optional)**")
            st.caption(
                "One rule per line, in plain language: \"if fever and cough then flu\" or "
                "\"si fièvre et toux alors grippe\". Matched by keyword against your column "
                "names — this is a simple parser for now, an LLM-based version is a natural "
                "next step once this is validated."
            )
            custom_background_text = st.text_area(
                "Background knowledge",
                key="custom_ilp_background_text",
                placeholder="if fever and cough then flu\nsi diabete et hypertension alors risque_eleve",
                height=100,
                label_visibility="collapsed",
            )

            try:
                _custom_gemini_key = st.secrets.get("GEMINI_API_KEY", "")
            except Exception:  # noqa: BLE001 — no secrets.toml at all, e.g. fresh install
                _custom_gemini_key = ""

            custom_use_llm = st.checkbox(
                "Use AI to parse background knowledge (more flexible phrasing, needs a free API key)",
                value=False,
                disabled=not _custom_gemini_key,
                key="custom_ilp_use_llm",
                help=(
                    "Reads GEMINI_API_KEY from .streamlit/secrets.toml. Still validates every "
                    "predicate the model produces against your known columns before trusting it — "
                    "same safety net as the keyword parser."
                    if _custom_gemini_key
                    else "Add a free GEMINI_API_KEY (aistudio.google.com/apikey) to .streamlit/secrets.toml to enable this."
                ),
            )

            if not custom_positive_values:
                st.warning("Pick at least one positive value for the target column to continue.")
            elif not custom_feature_columns:
                st.warning("Pick at least one feature column to continue.")
            else:
                plan, work_df = build_conversion_plan(
                    custom_df,
                    custom_feature_columns,
                    custom_target_column,
                    custom_positive_values,
                )

                known_predicates = [plan.target_predicate] + [cp.predicate for cp in plan.feature_plans]

                background_rules: list[str] = []
                background_warnings: list[str] = []
                if custom_use_llm and custom_background_text.strip():
                    from core.llm_background import (
                        LLMParsingUnavailable,
                        parse_background_text_with_llm,
                    )

                    try:
                        with st.spinner("Parsing background knowledge with AI…"):
                            background_rules, background_warnings = parse_background_text_with_llm(
                                custom_background_text,
                                known_predicates,
                                api_key=_custom_gemini_key,
                            )
                        st.caption("✨ Parsed with AI")
                    except LLMParsingUnavailable as exc:
                        st.caption(f"⚠️ AI parsing unavailable ({exc}) — falling back to keyword parsing")
                        background_rules, background_warnings = parse_background_text(
                            custom_background_text, known_predicates
                        )
                else:
                    background_rules, background_warnings = parse_background_text(
                        custom_background_text, known_predicates
                    )

                for warning in background_warnings:
                    st.caption(f"⚠️ {warning}")

                st.write("")
                st.markdown(
                    f"**{len(plan.sample_ids)} samples** · "
                    f"**{len(plan.positive_ids)} positive** / **{len(plan.negative_ids)} negative** "
                    f"for `{plan.target_predicate}` · {len(plan.feature_plans)} feature predicates"
                )

                popper_files = build_popper_dataset(plan, work_df, background_rules)
                andante_text = build_andante_dataset(plan, work_df, background_rules)

                # Rendering thousands of syntax-highlighted lines inside
                # st.code() can noticeably stall the browser tab on wide
                # tables (many feature columns => one fact per row per
                # column). Cap what's actually rendered; the download
                # button below always carries the full, untruncated file.
                _PREVIEW_LINE_CAP = 400

                def _preview_text(full_text: str) -> str:
                    lines = full_text.splitlines()
                    if len(lines) <= _PREVIEW_LINE_CAP:
                        return full_text
                    shown = "\n".join(lines[:_PREVIEW_LINE_CAP])
                    return (
                        f"{shown}\n\n% … {len(lines) - _PREVIEW_LINE_CAP} more lines — "
                        "use the download button to get the full file"
                    )

                st.write("")
                popper_preview_tab, andante_preview_tab = st.tabs(["Popper dataset", "Andante dataset"])
                with popper_preview_tab:
                    popper_file_tab = st.radio(
                        "File",
                        options=["bias.pl", "bk.pl", "exs.pl"],
                        horizontal=True,
                        key="custom_ilp_popper_file_tab",
                        label_visibility="collapsed",
                    )
                    with st.container(height=280, border=True):
                        st.code(_preview_text(popper_files[popper_file_tab]), language="prolog", line_numbers=True)
                    dl_cols = st.columns(3)
                    for dl_col, fname in zip(dl_cols, ["bias.pl", "bk.pl", "exs.pl"]):
                        with dl_col:
                            st.download_button(
                                f"⬇ {fname}",
                                data=popper_files[fname],
                                file_name=fname,
                                mime="text/x-prolog",
                                use_container_width=True,
                                key=f"custom_ilp_dl_{fname}",
                            )
                with andante_preview_tab:
                    with st.container(height=280, border=True):
                        st.code(_preview_text(andante_text), language="prolog", line_numbers=True)
                    st.download_button(
                        "⬇ Download as .pl",
                        data=andante_text,
                        file_name=f"{plan.target_predicate}.pl",
                        mime="text/x-prolog",
                        use_container_width=True,
                        key="custom_ilp_dl_andante",
                    )

                st.divider()

                st.markdown('<div class="section-title">Learn from this data</div>', unsafe_allow_html=True)
                st.markdown(
                    '<div class="section-caption">Runs for real, right here — the same centralized runner Try & Learn uses</div>',
                    unsafe_allow_html=True,
                )

                learn_col_1, learn_col_2 = st.columns([1, 1])
                with learn_col_1:
                    custom_system = st.radio(
                        "System",
                        options=["Popper", "Andante"],
                        horizontal=True,
                        key="custom_ilp_system",
                    )
                with learn_col_2:
                    st.write("")
                    custom_run_clicked = st.button(
                        f"▶ Run {custom_system} on this data",
                        type="primary",
                        use_container_width=True,
                        key="custom_ilp_run",
                    )

                if custom_run_clicked:
                    custom_dataset_name = "custom_" + sanitize_identifier(
                        custom_file.name.rsplit(".", 1)[0], fallback="dataset"
                    )

                    if custom_system == "Popper":
                        dataset_dir = DATASETS_DIRECTORY / custom_dataset_name
                        dataset_dir.mkdir(parents=True, exist_ok=True)
                        for fname, content in popper_files.items():
                            (dataset_dir / fname).write_text(content, encoding="utf-8")
                    else:
                        andante_dir = DATASETS_DIRECTORY / "andante"
                        andante_dir.mkdir(parents=True, exist_ok=True)
                        (andante_dir / f"{custom_dataset_name}.pl").write_text(
                            andante_text, encoding="utf-8"
                        )

                    from core.launcher import ExperimentLauncher
                    from core.experiment import ExperimentConfig

                    custom_learner = "andante" if custom_system == "Andante" else "popper"
                    custom_run_error: str | None = None
                    custom_experiment_id: int | None = None

                    with st.status(f"Running {custom_system} on your data…", expanded=True) as custom_status:
                        st.write(
                            f"Loading `{custom_dataset_name}` — {len(plan.positive_ids)} positive, "
                            f"{len(plan.negative_ids)} negative examples"
                        )
                        st.write("Launching a centralized run (no federation, single process)…")
                        try:
                            custom_config = ExperimentConfig(
                                approach="centralized",
                                dataset=custom_dataset_name,
                                number_of_clients=1,
                                partition_strategy="iid",
                                learner=custom_learner,
                            )
                            custom_experiment_id = ExperimentLauncher().run(custom_config)
                            custom_status.update(label="Run complete", state="complete", expanded=False)
                        except Exception as exc:  # noqa: BLE001 — surface any solver error to the user
                            custom_run_error = str(exc)
                            custom_status.update(label="Run failed", state="error", expanded=True)

                    if custom_run_error:
                        st.session_state["custom_ilp_result"] = {
                            "system": custom_system,
                            "dataset": custom_dataset_name,
                            "error": custom_run_error,
                        }
                    else:
                        with get_connection() as _custom_conn:
                            _custom_row = _custom_conn.execute(
                                """
                                SELECT solution, solution_found, total_time_seconds, number_of_programs,
                                       tp, fn, tn, fp
                                FROM server_results
                                WHERE experiment_id = ?
                                """,
                                (custom_experiment_id,),
                            ).fetchone()
                        st.session_state["custom_ilp_result"] = {
                            "system": custom_system,
                            "dataset": custom_dataset_name,
                            "error": None,
                            **(dict(_custom_row) if _custom_row else {}),
                        }
                        # Chat context (below) references the current known
                        # predicates and their meaning, kept alongside the
                        # result so it survives into later reruns (e.g. when
                        # the user sends a chat message, which reruns the
                        # whole script but custom_run_clicked is False again).
                        st.session_state["custom_ilp_predicate_glossary"] = {
                            cp.predicate: (
                                f"true iff {cp.original_name!r} >= {cp.threshold:.4g}"
                                if cp.threshold is not None
                                else (
                                    f"true iff {cp.original_name!r} is a 'yes'-like value"
                                    if cp.kind == "boolean"
                                    else f"{cp.original_name!r}'s raw value"
                                )
                            )
                            for cp in plan.feature_plans
                        }

                # -------------------------------------------------------
                # Persisted result display — reads from session_state (not
                # just inside the `if custom_run_clicked` branch) so it
                # stays visible across reruns, e.g. while chatting below.
                # -------------------------------------------------------
                _stored_custom_result = st.session_state.get("custom_ilp_result")
                if _stored_custom_result:
                    if _stored_custom_result.get("error"):
                        st.error(f"Run failed: {_stored_custom_result['error']}")
                    else:
                        st.success("Run complete")
                        result_metric_cols = st.columns(4)
                        tp, fn, tn, fp = (
                            _stored_custom_result.get("tp"),
                            _stored_custom_result.get("fn"),
                            _stored_custom_result.get("tn"),
                            _stored_custom_result.get("fp"),
                        )
                        if None not in (tp, fn, tn, fp) and (tp + fn + tn + fp) > 0:
                            accuracy = (tp + tn) / (tp + fn + tn + fp)
                            precision = tp / (tp + fp) if (tp + fp) else 0.0
                            recall = tp / (tp + fn) if (tp + fn) else 0.0
                            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
                            with result_metric_cols[0]:
                                st.metric("Accuracy", f"{accuracy:.0%}")
                            with result_metric_cols[1]:
                                st.metric("Precision", f"{precision:.0%}")
                            with result_metric_cols[2]:
                                st.metric("Recall", f"{recall:.0%}")
                            with result_metric_cols[3]:
                                st.metric("F1", f"{f1:.0%}")
                        st.markdown("**Learned hypothesis**")
                        st.code(_stored_custom_result.get("solution") or "(no hypothesis found)", language="prolog")

                # -------------------------------------------------------
                # Chat with the AI about this dataset — contextualized
                # with the current predicate glossary and the last run's
                # result (if any), read from session_state above.
                # -------------------------------------------------------
                st.divider()
                st.markdown('<div class="section-title">Ask the AI about this data</div>', unsafe_allow_html=True)

                if not _custom_gemini_key:
                    st.info(
                        "Add a free `GEMINI_API_KEY` (aistudio.google.com/apikey) to "
                        "`.streamlit/secrets.toml` to enable this chat.",
                        icon="💬",
                    )
                else:
                    chat_history_key = "custom_ilp_chat_history"
                    if chat_history_key not in st.session_state:
                        st.session_state[chat_history_key] = []

                    for msg in st.session_state[chat_history_key]:
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])

                    custom_chat_input = st.chat_input(
                        "Ask about your columns, the generated predicates, or the last run…"
                    )
                    if custom_chat_input:
                        st.session_state[chat_history_key].append(
                            {"role": "user", "content": custom_chat_input}
                        )
                        with st.chat_message("user"):
                            st.markdown(custom_chat_input)

                        glossary = st.session_state.get("custom_ilp_predicate_glossary", {})
                        stored_result = st.session_state.get("custom_ilp_result")
                        context_lines = [
                            f"The user uploaded a table with {len(plan.sample_ids)} samples.",
                            f"Target predicate: {plan.target_predicate}/1 "
                            f"({len(plan.positive_ids)} positive, {len(plan.negative_ids)} negative).",
                            "Feature predicates generated from the table's columns:",
                        ]
                        for pred, meaning in glossary.items():
                            context_lines.append(f"  - {pred}: {meaning}")
                        if stored_result and not stored_result.get("error"):
                            context_lines.append(
                                f"Last run: {stored_result.get('system')} found hypothesis "
                                f"`{stored_result.get('solution') or '(none)'}` "
                                f"(tp={stored_result.get('tp')}, fn={stored_result.get('fn')}, "
                                f"tn={stored_result.get('tn')}, fp={stored_result.get('fp')})."
                            )
                        elif stored_result and stored_result.get("error"):
                            context_lines.append(f"Last run failed: {stored_result['error']}")

                        from core.llm_background import chat_reply

                        with st.chat_message("assistant"):
                            try:
                                with st.spinner("Thinking…"):
                                    assistant_text = chat_reply(
                                        st.session_state[chat_history_key],
                                        context="\n".join(context_lines),
                                        api_key=_custom_gemini_key,
                                    )
                                st.markdown(assistant_text)
                                st.session_state[chat_history_key].append(
                                    {"role": "assistant", "content": assistant_text}
                                )
                            except Exception as exc:  # noqa: BLE001 — surface API errors inline, don't crash
                                st.error(f"Chat failed: {exc}")


