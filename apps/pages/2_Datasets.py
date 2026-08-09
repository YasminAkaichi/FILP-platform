from __future__ import annotations

import re
import sys
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------
# Project setup
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DATASETS_DIRECTORY = PROJECT_ROOT / "datasets"


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Dataset Explorer | FILP",
    page_icon="",
    layout="wide",
)

# Same logo, same fixed slot above the sidebar navigation on every page.
LOGO_PATH = PROJECT_ROOT / "assets" / "filp_logo.svg"

if hasattr(st, "logo"):
    try:
        st.logo(str(LOGO_PATH), size="large")
    except Exception:
        pass


# ---------------------------------------------------------------------
# Visual design system — same palette as the Experiments page, so the
# two pages feel like one app rather than two different tools.
# ---------------------------------------------------------------------

PALETTE = {
    "bg_card": "#F6F8FC",
    "border": "#E2E8F5",
    "text_muted": "#5B6472",
    "text": "#1F2430",
    "primary": "#5B7FDE",
    "primary_soft": "#EAF0FE",
    "success": "#2F9E63",
    "success_soft": "#E7F6EE",
    "warning": "#C98A1F",
    "warning_soft": "#FCF1DE",
    "error": "#D1554B",
    "error_soft": "#FBEAE8",
    "neutral": "#8A93A3",
    "neutral_soft": "#EEF1F6",
}


def inject_style() -> None:
    # NOTE: every generated HTML snippet below is built as a single
    # line with no leading indentation. Streamlit's markdown renderer
    # treats a blank / whitespace-only line followed by 4+ spaces of
    # indentation as a code block, which silently breaks custom HTML
    # cards if you're not careful with multiline f-strings.
    st.markdown(
        f"""
        <style>
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 14px !important;
        }}

        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin: 4px 0 8px 0;
        }}
        .metric-card {{
            background: {PALETTE["bg_card"]};
            border: 1px solid {PALETTE["border"]};
            border-radius: 12px;
            padding: 14px 16px;
        }}
        .metric-card .metric-label {{
            font-size: 0.78rem;
            color: {PALETTE["text_muted"]};
            font-weight: 500;
            margin-bottom: 4px;
        }}
        .metric-card .metric-value {{
            font-size: 1.35rem;
            color: {PALETTE["text"]};
            font-weight: 600;
            line-height: 1.2;
        }}

        .section-title {{
            font-size: 1.05rem;
            font-weight: 600;
            color: {PALETTE["text"]};
            margin: 6px 0 2px 0;
        }}
        .section-caption {{
            font-size: 0.85rem;
            color: {PALETTE["text_muted"]};
            margin-bottom: 10px;
        }}

        .chip-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 6px 0 14px 0;
        }}
        .chip {{
            border-radius: 999px;
            padding: 4px 12px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        .chip-neutral {{ background: {PALETTE["neutral_soft"]}; color: {PALETTE["text"]}; }}
        .chip-primary {{ background: {PALETTE["primary_soft"]}; color: {PALETTE["primary"]}; }}
        .chip-success {{ background: {PALETTE["success_soft"]}; color: {PALETTE["success"]}; }}
        .chip-error {{ background: {PALETTE["error_soft"]}; color: {PALETTE["error"]}; }}
        .chip b {{ font-weight: 500; opacity: 0.7; margin-right: 4px; }}

        .balance-bar {{
            display: flex;
            height: 10px;
            width: 100%;
            border-radius: 999px;
            overflow: hidden;
            background: {PALETTE["neutral_soft"]};
            margin: 6px 0 4px 0;
        }}
        .balance-pos {{ background: {PALETTE["success"]}; }}
        .balance-neg {{ background: {PALETTE["error"]}; }}
        .balance-caption {{
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: {PALETTE["text_muted"]};
        }}

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

        div[data-testid="stCodeBlock"] {{
            max-height: 480px;
            overflow-y: auto;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_grid(items: list[dict]) -> None:
    card_parts = []

    for item in items:
        card_parts.append(
            '<div class="metric-card">'
            f'<div class="metric-label">{item["label"]}</div>'
            f'<div class="metric-value">{item["value"]}</div>'
            "</div>"
        )

    cards = "".join(card_parts)
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)


def render_chips(pairs: list[tuple[str, str]], variant: str = "neutral") -> None:
    chips = "".join(
        f'<span class="chip chip-{variant}"><b>{label}</b>{value}</span>'
        for label, value in pairs
    )
    st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)


def render_balance_bar(positive: int, negative: int) -> None:
    total = positive + negative

    if total == 0:
        pos_pct, neg_pct = 0, 0
    else:
        pos_pct = round(100 * positive / total)
        neg_pct = 100 - pos_pct

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


# ---------------------------------------------------------------------
# Data helpers (unchanged behaviour)
# ---------------------------------------------------------------------

def get_available_datasets() -> list[str]:
    if not DATASETS_DIRECTORY.is_dir():
        return []

    return sorted(
        directory.name
        for directory in DATASETS_DIRECTORY.iterdir()
        if directory.is_dir()
        and directory.name != "generated"
        and (directory / "exs.pl").is_file()
        and (directory / "bk.pl").is_file()
        and (directory / "bias.pl").is_file()
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
    positive_examples = []
    negative_examples = []

    for line in clean_prolog_lines(examples_text):
        if line.startswith("pos("):
            positive_examples.append(line)
        elif line.startswith("neg("):
            negative_examples.append(line)

    return positive_examples, negative_examples


def extract_target_predicates(bias_text: str) -> list[str]:
    targets = []

    patterns = [
        r"head_pred\(([^)]+)\)",
        r"target\(([^)]+)\)",
    ]

    for pattern in patterns:
        for match in re.findall(pattern, bias_text):
            if match not in targets:
                targets.append(match)

    return targets


def count_facts(background_text: str) -> int:
    return sum(1 for line in clean_prolog_lines(background_text) if line.endswith("."))


def format_dataset_name(dataset_name: str) -> str:
    return dataset_name.replace("_", " ").title()


# ---------------------------------------------------------------------
# Page body
# ---------------------------------------------------------------------

inject_style()

st.title("Dataset Explorer")
st.caption(
    "Browse the logical datasets used by FILP — examples, background "
    "knowledge and language bias, exactly as given to the learner."
)

datasets = get_available_datasets()

if not datasets:
    st.error("No valid dataset was found in the datasets directory.")
    st.stop()


# --- Sidebar: dataset picker + always-visible stats ------------------

with st.sidebar:
    st.markdown('<div class="section-title">Datasets</div>', unsafe_allow_html=True)

    selected_dataset = st.radio(
        "Dataset",
        options=datasets,
        format_func=format_dataset_name,
        label_visibility="collapsed",
    )

    st.divider()

    dataset_directory = DATASETS_DIRECTORY / selected_dataset

    examples_text = read_text_file(dataset_directory / "exs.pl")
    background_text = read_text_file(dataset_directory / "bk.pl")
    bias_text = read_text_file(dataset_directory / "bias.pl")

    positive_examples, negative_examples = split_examples(examples_text)
    target_predicates = extract_target_predicates(bias_text)
    background_fact_count = count_facts(background_text)
    background_line_count = len(background_text.splitlines())

    st.markdown('<div class="section-title">At a glance</div>', unsafe_allow_html=True)

    render_metric_grid(
        [
            {
                "label": "Examples",
                "value": len(positive_examples) + len(negative_examples),
            },
            {"label": "Positive", "value": len(positive_examples)},
            {"label": "Negative", "value": len(negative_examples)},
            {"label": "Background facts", "value": background_fact_count},
        ]
    )

    render_balance_bar(len(positive_examples), len(negative_examples))

    if target_predicates:
        st.markdown(
            '<div class="section-title" style="margin-top:14px;">Target predicate(s)</div>',
            unsafe_allow_html=True,
        )
        render_chips([(t, "") for t in target_predicates], variant="primary")


# --- Main area ---------------------------------------------------------

st.markdown(
    f'<div class="intro-card">A dataset is a set of Prolog files: '
    f"<b>positive / negative examples</b> define the concept to learn, "
    f"<b>background knowledge</b> gives the learner facts and relations "
    f"to reason over, and the <b>language bias</b> restricts the shape "
    f"of hypotheses Popper is allowed to construct.</div>",
    unsafe_allow_html=True,
)

header_left, header_right = st.columns([4, 2])

with header_left:
    st.markdown(
        f'<div class="section-title" style="font-size:1.2rem;">{format_dataset_name(selected_dataset)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="section-caption">{dataset_directory}</div>',
        unsafe_allow_html=True,
    )

with header_right:
    render_chips(
        [
            ("Examples", str(len(positive_examples) + len(negative_examples))),
            ("Facts", str(background_fact_count)),
        ],
        variant="neutral",
    )

examples_tab, background_tab, bias_tab = st.tabs(
    ["Examples", "Background knowledge", "Language bias"]
)


# --- Examples tab --------------------------------------------------------

with examples_tab:
    code_column, stats_column = st.columns([3, 1])

    with stats_column:
        with st.container(border=True):
            st.markdown('<div class="section-title">Counts</div>', unsafe_allow_html=True)
            render_metric_grid(
                [
                    {"label": "Positive", "value": len(positive_examples)},
                    {"label": "Negative", "value": len(negative_examples)},
                    {
                        "label": "Total",
                        "value": len(positive_examples) + len(negative_examples),
                    },
                ]
            )
            render_balance_bar(len(positive_examples), len(negative_examples))
            st.caption("Source: `exs.pl`")

    with code_column:
        positive_view, negative_view = st.tabs(
            [f"Positive ({len(positive_examples)})", f"Negative ({len(negative_examples)})"]
        )

        with positive_view:
            st.caption("Expected to be entailed by the learned hypothesis.")
            if positive_examples:
                st.code("\n".join(positive_examples), language="prolog", line_numbers=True)
            else:
                st.warning("No positive example was found in exs.pl.")

        with negative_view:
            st.caption("Must NOT be entailed by the learned hypothesis.")
            if negative_examples:
                st.code("\n".join(negative_examples), language="prolog", line_numbers=True)
            else:
                st.warning("No negative example was found in exs.pl.")

        with st.expander("View the complete exs.pl file"):
            st.code(examples_text, language="prolog", line_numbers=True)


# --- Background knowledge tab --------------------------------------------

with background_tab:
    code_column, stats_column = st.columns([3, 1])

    with stats_column:
        with st.container(border=True):
            st.markdown('<div class="section-title">Counts</div>', unsafe_allow_html=True)
            render_metric_grid(
                [
                    {"label": "Facts", "value": background_fact_count},
                    {"label": "Lines", "value": background_line_count},
                ]
            )
            st.caption("Source: `bk.pl`")

    with code_column:
        st.caption(
            "Facts and, depending on the dataset, reusable rules that "
            "describe the domain — objects, relations, attributes."
        )

        background_lines = background_text.splitlines()

        filter_col, size_col, page_col = st.columns([2, 1, 1])

        with filter_col:
            search_term = st.text_input(
                "Search",
                placeholder="Filter lines (e.g. a predicate name)…",
                key=f"bk_search_{selected_dataset}",
            )

        with size_col:
            preview_size = st.selectbox(
                "Lines per page",
                options=[50, 100, 200, 500],
                index=1,
                key=f"bk_page_size_{selected_dataset}",
            )

        display_lines = (
            [line for line in background_lines if search_term.lower() in line.lower()]
            if search_term
            else background_lines
        )
        number_of_lines = len(display_lines)
        number_of_pages = max(1, (number_of_lines + preview_size - 1) // preview_size)

        with page_col:
            selected_page = st.number_input(
                "Page",
                min_value=1,
                max_value=number_of_pages,
                value=1,
                step=1,
                key=f"bk_page_{selected_dataset}",
            )

        start_index = (int(selected_page) - 1) * preview_size
        end_index = min(start_index + preview_size, number_of_lines)
        visible_background = "\n".join(display_lines[start_index:end_index])

        st.caption(
            f"Showing lines {start_index + 1}–{end_index} of {number_of_lines}"
            + (f" (filtered from {background_line_count})" if search_term else "")
        )

        st.code(visible_background or "—", language="prolog", line_numbers=True)


# --- Bias tab --------------------------------------------------------------

with bias_tab:
    code_column, stats_column = st.columns([3, 1])

    with stats_column:
        with st.container(border=True):
            st.markdown('<div class="section-title">Target predicate(s)</div>', unsafe_allow_html=True)
            if target_predicates:
                render_chips([(t, "") for t in target_predicates], variant="primary")
            else:
                st.caption("None detected.")
            st.caption("Source: `bias.pl`")

    with code_column:
        st.caption(
            "Predicates and structural limits (variables, clauses, body "
            "literals) that Popper may use while building hypotheses."
        )
        st.code(bias_text or "—", language="prolog", line_numbers=True)