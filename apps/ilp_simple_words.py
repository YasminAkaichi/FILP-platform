"""ILP in simple words: the light, story-style tab of the ILP page (next to the
formal Overview tab).

The family example is computed for real: each candidate rule is evaluated on
the training examples and on unseen cases, so the reader sees why the
'cheating' rule fails and why the shortest correct rule wins.
"""

from __future__ import annotations

import streamlit as st

PALETTE = {
    "bg_card": "#F3F4F6",
    "border": "#E5E7EB",
    "text_muted": "#5B6472",
    "text": "#1F2430",
    "primary": "#1B2A4C",
    "ok": "#1E7A4C",
    "ok_soft": "#E6F4EC",
    "bad": "#B42318",
    "bad_soft": "#FDECEA",
}


def render_simple_words() -> None:

    st.markdown(
        f"""
        <style>
        .sw-hero {{
            border: 1px solid {PALETTE["border"]};
            background: {PALETTE["bg_card"]};
            border-radius: 18px;
            padding: 30px 34px;
            margin-bottom: 8px;
        }}
        .sw-hero h1 {{
            margin: 0 0 6px 0;
            font-size: 2.1rem;
            color: {PALETTE["primary"]};
            line-height: 1.2;
        }}
        .sw-hero p {{
            margin: 0;
            font-size: 1.05rem;
            color: {PALETTE["text_muted"]};
        }}
        .sw-kicker {{
            font-size: 0.78rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: {PALETTE["text_muted"]};
            font-weight: 700;
            margin-top: 34px;
            margin-bottom: 2px;
        }}
        .sw-title {{
            font-size: 1.45rem;
            font-weight: 700;
            color: {PALETTE["primary"]};
            margin: 0 0 6px 0;
        }}
        .sw-lead {{
            color: {PALETTE["text_muted"]};
            font-size: 1rem;
            margin-bottom: 14px;
        }}
        .sw-card {{
            border: 1px solid {PALETTE["border"]};
            background: #FFFFFF;
            border-radius: 14px;
            padding: 18px 20px;
            height: 100%;
        }}
        .sw-card h4 {{
            margin: 0 0 6px 0;
            font-size: 1.02rem;
            color: {PALETTE["primary"]};
        }}
        .sw-card p, .sw-card li {{
            color: {PALETTE["text"]};
            font-size: 0.96rem;
        }}
        .sw-flow {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
            margin: 10px 0 6px 0;
            font-size: 0.95rem;
        }}
        .sw-chip {{
            border: 1px solid {PALETTE["border"]};
            background: {PALETTE["bg_card"]};
            border-radius: 999px;
            padding: 5px 13px;
            color: {PALETTE["text"]};
        }}
        .sw-chip.dark {{
            background: {PALETTE["primary"]};
            border-color: {PALETTE["primary"]};
            color: #FFFFFF;
        }}
        .sw-arrow {{ color: {PALETTE["text_muted"]}; font-size: 1.2rem; }}
        .sw-rule {{
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            background: {PALETTE["primary"]};
            color: #FFFFFF;
            border-radius: 12px;
            padding: 14px 18px;
            font-size: 0.98rem;
            white-space: pre-wrap;
        }}
        table.sw-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95rem;
        }}
        table.sw-table th {{
            text-align: left;
            color: {PALETTE["text_muted"]};
            font-weight: 600;
            border-bottom: 1px solid {PALETTE["border"]};
            padding: 8px 10px;
        }}
        table.sw-table td {{
            border-bottom: 1px solid {PALETTE["border"]};
            padding: 8px 10px;
            color: {PALETTE["text"]};
        }}
        .sw-ok {{ color: {PALETTE["ok"]}; font-weight: 700; }}
        .sw-bad {{ color: {PALETTE["bad"]}; font-weight: 700; }}
        .sw-verdict {{
            border-radius: 12px;
            padding: 12px 16px;
            font-size: 0.97rem;
            margin-top: 10px;
        }}
        .sw-verdict.ok {{ background: {PALETTE["ok_soft"]}; color: {PALETTE["ok"]}; }}
        .sw-verdict.bad {{ background: {PALETTE["bad_soft"]}; color: {PALETTE["bad"]}; }}
        .sw-note {{
            border-left: 4px solid {PALETTE["primary"]};
            background: {PALETTE["bg_card"]};
            border-radius: 0 12px 12px 0;
            padding: 12px 16px;
            color: {PALETTE["text"]};
            margin-top: 12px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


    def section(kicker: str, title: str, lead: str = "") -> None:
        st.markdown(f'<div class="sw-kicker">{kicker}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sw-title">{title}</div>', unsafe_allow_html=True)
        if lead:
            st.markdown(f'<div class="sw-lead">{lead}</div>', unsafe_allow_html=True)


    # ---------------------------------------------------------------------
    # The family example
    # ---------------------------------------------------------------------

    PARENT = {("rose", "marie"), ("marie", "paul"), ("marie", "julie"), ("paul", "lea")}
    PEOPLE = sorted({name for pair in PARENT for name in pair})

    POSITIVE = [("rose", "paul"), ("marie", "lea")]
    NEGATIVE = [("marie", "paul"), ("lea", "marie")]
    UNSEEN = [("rose", "julie", True), ("paul", "marie", False), ("rose", "lea", False)]


    def has_child(x: str) -> bool:
        return any(p == x for p, _ in PARENT)


    def rule_anything(x: str, z: str) -> bool:
        return True


    def rule_one_condition(x: str, z: str) -> bool:
        return has_child(x)


    def rule_two_conditions(x: str, z: str) -> bool:
        return any((x, y) in PARENT and (y, z) in PARENT for y in PEOPLE)


    def rule_by_heart(x: str, z: str) -> bool:
        return (x, z) in POSITIVE


    HYPOTHESES = {
        "1. No condition": {
            "rule": "grand_parent(X, Z).",
            "fn": rule_anything,
            "says": "Everybody is a grandparent of everybody.",
        },
        "2. One condition": {
            "rule": "grand_parent(X, Z) :- parent(X, Y).",
            "fn": rule_one_condition,
            "says": "Anyone who has a child is a grandparent of anyone.",
        },
        "3. Two conditions": {
            "rule": "grand_parent(X, Z) :-\n    parent(X, Y), parent(Y, Z).",
            "fn": rule_two_conditions,
            "says": "X is a parent of someone who is a parent of Z.",
        },
        "4. Learned by heart": {
            "rule": "grand_parent(rose, paul).\ngrand_parent(marie, lea).",
            "fn": rule_by_heart,
            "says": "Just the two examples, copied.",
        },
    }


    def mark(value: bool, good: bool) -> str:
        """A check or a cross, green when it is what we wanted."""
        symbol = "✓" if value else "✗"
        return f'<span class="{"sw-ok" if good else "sw-bad"}">{symbol}</span>'


    # ---------------------------------------------------------------------
    # Page
    # ---------------------------------------------------------------------

    st.markdown(
        """
        <div class="sw-hero">
          <h1>What if your computer could learn rules?</h1>
          <p>Inductive Logic Programming (ILP) in simple words: how it works,
          and how it compares with the machine learning you already know.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- 1. Deduction vs induction --------------------------------------
    section(
        "Step 1",
        "Deduction goes one way, induction goes the other",
        "Logic programming (Prolog) <b>deduces</b>: it applies rules to facts. ILP does the opposite.",
    )

    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        st.markdown(
            """
            <div class="sw-card">
              <h4>Prolog: deduction</h4>
              <div class="sw-flow">
                <span class="sw-chip">Rules</span><span class="sw-arrow">+</span>
                <span class="sw-chip">Facts</span><span class="sw-arrow">→</span>
                <span class="sw-chip dark">Conclusions</span>
              </div>
              <p>You write the rules. The machine derives what follows.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            """
            <div class="sw-card">
              <h4>ILP: induction</h4>
              <div class="sw-flow">
                <span class="sw-chip">Facts</span><span class="sw-arrow">+</span>
                <span class="sw-chip">Examples</span><span class="sw-arrow">→</span>
                <span class="sw-chip dark">Rules</span>
              </div>
              <p>You show concrete cases. The machine guesses the general law that explains them.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="sw-note"><b>In one sentence:</b> ILP learns logic programs from examples.</div>',
        unsafe_allow_html=True,
    )

    # ---- 2. Ingredients ---------------------------------------------------
    section(
        "Step 2",
        "The ingredients",
        "Every ILP problem has the same four pieces.",
    )

    ing_1, ing_2, ing_3, ing_4 = st.columns(4, gap="small")
    ingredients = [
        (ing_1, "Background knowledge (B)", "What we already know, for example the <code>parent(…)</code> facts."),
        (ing_2, "Positive examples (E+)", "What <b>must</b> be true."),
        (ing_3, "Negative examples (E−)", "What must be <b>false</b>."),
        (ing_4, "Hypothesis (H)", "The rules the machine learns."),
    ]
    for column, title, text in ingredients:
        with column:
            st.markdown(
                f'<div class="sw-card"><h4>{title}</h4><p>{text}</p></div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <div class="sw-note">
          A good hypothesis <b>explains every positive example</b> (B + H ⊨ E+) and
          <b>none of the negative ones</b> (B + H ⊭ E−). Explain everything, without
          saying anything silly.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- 3. The family ----------------------------------------------------
    section(
        "Step 3",
        "Rose's family",
        "The mission: find the rule for <i>grand-parent</i>, with only four examples. "
        "(A neural network would ask for thousands.)",
    )

    fam_left, fam_right = st.columns([1, 1.2], gap="large")

    with fam_left:
        st.markdown("**Background knowledge (B)**")
        st.code(
            "\n".join(f"parent({p}, {c})." for p, c in sorted(PARENT)),
            language="prolog",
        )
        st.markdown(
            """
            <div class="sw-card">
              <p style="margin:0;">Rose → Marie → Paul and Julie. Paul → Léa.<br>
              <span style="color:#5B6472;">Rose is Marie's parent; Marie is Paul's and Julie's parent; Paul is Léa's parent.</span></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with fam_right:
        rows = ""
        for x, z in POSITIVE:
            rows += (
                f"<tr><td><code>grand_parent({x}, {z})</code></td>"
                f'<td><span class="sw-ok">✓ must be true</span></td></tr>'
            )
        for x, z in NEGATIVE:
            rows += (
                f"<tr><td><code>grand_parent({x}, {z})</code></td>"
                f'<td><span class="sw-bad">✗ must be false</span></td></tr>'
            )
        st.markdown("**Examples (E+ and E−)**")
        st.markdown(
            f'<table class="sw-table"><tr><th>Example</th><th>What we want</th></tr>{rows}</table>',
            unsafe_allow_html=True,
        )

    # ---- 4. The search (interactive) -------------------------------------
    section(
        "Step 4",
        "The search: from too general to just right",
        "The machine starts with a rule that is too general and adds one condition at a time. "
        "This is called <b>refinement</b>. Pick a rule to check it on the examples.",
    )

    choice = st.radio(
        "Candidate rule",
        options=list(HYPOTHESES),
        horizontal=True,
        label_visibility="collapsed",
        key="simple_words_rule",
    )
    selected = HYPOTHESES[choice]
    function = selected["fn"]

    rule_col, check_col = st.columns([1, 1.3], gap="large")

    with rule_col:
        st.markdown(f'<div class="sw-rule">{selected["rule"]}</div>', unsafe_allow_html=True)
        st.caption(f"In words: {selected['says']}")

    with check_col:
        rows = ""
        pos_ok = neg_ok = 0
        for x, z in POSITIVE:
            covered = function(x, z)
            pos_ok += covered
            rows += (
                f"<tr><td><code>grand_parent({x}, {z})</code></td>"
                f"<td>should be true</td><td>{mark(covered, covered)} {'covered' if covered else 'missed'}</td></tr>"
            )
        for x, z in NEGATIVE:
            covered = function(x, z)
            neg_ok += not covered
            rows += (
                f"<tr><td><code>grand_parent({x}, {z})</code></td>"
                f"<td>should be false</td><td>{mark(not covered, not covered)} {'wrongly covered' if covered else 'rejected'}</td></tr>"
            )
        st.markdown(
            f'<table class="sw-table"><tr><th>Example</th><th>Expected</th><th>This rule</th></tr>{rows}</table>',
            unsafe_allow_html=True,
        )

    perfect = pos_ok == len(POSITIVE) and neg_ok == len(NEGATIVE)
    st.markdown(
        f'<div class="sw-verdict {"ok" if perfect else "bad"}">'
        f"{pos_ok}/{len(POSITIVE)} positive examples covered, "
        f"{len(NEGATIVE) - neg_ok}/{len(NEGATIVE)} negative examples wrongly covered. "
        f'{"A perfect score on the examples." if perfect else "Not good enough: the machine keeps refining."}'
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sw-note">Like machine learning, which adjusts its weights step by step, ILP adjusts a '
        "<b>rule</b>, piece by piece.</div>",
        unsafe_allow_html=True,
    )

    # ---- 5. The trap -------------------------------------------------------
    section(
        "Step 5",
        "The trap: learning by heart",
        "Rule 4 also has a perfect score on the examples. Test it on cases the machine has never seen.",
    )

    test_rows = ""
    for x, z, truth in UNSEEN:
        answer = function(x, z)
        good = answer == truth
        test_rows += (
            f"<tr><td><code>grand_parent({x}, {z})</code></td>"
            f"<td>{'true' if truth else 'false'}</td>"
            f"<td>{'true' if answer else 'false'}</td>"
            f"<td>{mark(good, good)}</td></tr>"
        )
    st.markdown(
        "**Unseen cases for the rule selected above**"
    )
    st.markdown(
        f'<table class="sw-table"><tr><th>New case</th><th>Truth</th><th>This rule says</th><th></th></tr>{test_rows}</table>',
        unsafe_allow_html=True,
    )

    unseen_ok = all(function(x, z) == truth for x, z, truth in UNSEEN)
    if choice == "4. Learned by heart":
        message = ("It memorized the examples and knows nothing about <code>grand_parent(rose, julie)</code>. "
                   "This is overfitting, the logic version.")
    elif unseen_ok:
        message = "It answers correctly on cases it has never seen: it learned the rule, not the examples."
    else:
        message = "It already fails on the training examples, so it is not the rule we are looking for."
    st.markdown(
        f'<div class="sw-verdict {"ok" if unseen_ok else "bad"}">{message}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sw-note"><b>The remedy: Occam\'s razor.</b> Among the rules that work, prefer the '
        "<b>shortest</b> one. Rule 3 is the shortest rule with a perfect score that is not a copy of the examples.</div>",
        unsafe_allow_html=True,
    )

    # ---- 6. ML vs ILP -----------------------------------------------------
    section(
        "Step 6",
        "Is it machine learning?",
        "Yes… and no. A lot is the same, and a few things are very different.",
    )

    same_col, diff_col = st.columns(2, gap="medium")
    with same_col:
        st.markdown(
            """
            <div class="sw-card">
              <h4>What is the same</h4>
              <ul>
                <li>It learns from <b>examples</b> (ML: labeled data, ILP: E+ and E−).</li>
                <li>It is often <b>classification</b>: true or false, like spam or not spam.</li>
                <li>It searches a space of hypotheses (ML: weights, ILP: rules).</li>
                <li>The goal is to <b>generalize</b> to cases never seen.</li>
                <li>Same enemy, overfitting, and same remedy: stay simple.</li>
                <li>It is evaluated on examples kept apart (a test set).</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with diff_col:
        st.markdown(
            """
            <div class="sw-card">
              <h4>What is different</h4>
              <table class="sw-table">
                <tr><th></th><th>ILP</th><th>Classic ML</th></tr>
                <tr><td>What it learns</td><td>readable rules</td><td>weights (numbers)</td></tr>
                <tr><td>Examples needed</td><td>a handful</td><td>thousands</td></tr>
                <tr><td>Domain knowledge</td><td>given directly (B)</td><td>hidden in the features</td></tr>
                <tr><td>Explainable?</td><td>yes, you read the rule</td><td>often a black box</td></tr>
                <tr><td>Images, sound, noise</td><td>hard</td><td>its playground</td></tr>
                <tr><td>The search</td><td>symbolic, piece by piece</td><td>continuous (gradient)</td></tr>
              </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="sw-note"><b>ILP: little data, a lot of meaning.</b> '
        "ML: a lot of data, a lot of power. An AI that learns… and tells you why.</div>",
        unsafe_allow_html=True,
    )

    # ---- 7. Tools and uses ------------------------------------------------
    section(
        "Step 7",
        "The names to know, and what it is used for",
    )

    tool_col, use_col = st.columns(2, gap="medium")
    with tool_col:
        st.markdown(
            """
            <div class="sw-card">
              <h4>Some ILP systems</h4>
              <table class="sw-table">
                <tr><td><b>FOIL</b></td><td>Quinlan, 1990</td></tr>
                <tr><td><b>Progol</b> and <b>Aleph</b></td><td>Muggleton, 1995</td></tr>
                <tr><td><b>Metagol</b></td><td>learns by filling templates of rules</td></tr>
                <tr><td><b>Popper</b></td><td>2021, very active today</td></tr>
              </table>
              <p style="margin-top:10px;color:#5B6472;">The name “Inductive Logic Programming” dates from 1991 (Stephen Muggleton).</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with use_col:
        st.markdown(
            """
            <div class="sw-card">
              <h4>What it is used for</h4>
              <ul>
                <li><b>Drug design:</b> which molecules are active, and why.</li>
                <li><b>Biology:</b> understanding genes and proteins.</li>
                <li><b>Program synthesis:</b> writing programs from examples.</li>
                <li><b>Explainable AI:</b> when every decision must be justified.</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---- 8. Next ---------------------------------------------------------
    section(
        "Next",
        "Try it yourself",
        "FILP lets you run several ILP systems on real datasets, and then learn together with other clients "
        "without sharing the data.",
    )

    next_1, next_2, next_3 = st.columns(3, gap="small")
    with next_1:
        st.markdown(
            '<div class="sw-card"><p style="margin:0;">Open the <b>Learning</b> tab of this page to run '
            "Popper, Popper 4, Andante or MaxSynth on a real dataset.</p></div>",
            unsafe_allow_html=True,
        )
    with next_2:
        st.page_link(
            "app_pages/01_Federated_Learning.py",
            label="Learn about federated learning",
            icon=":material/hub:",
            use_container_width=True,
        )
    with next_3:
        st.page_link(
            "app_pages/03_FILP_approaches.py",
            label="See the FILP approaches",
            icon=":material/compare_arrows:",
            use_container_width=True,
        )


# ---------------------------------------------------------------------
# Hand-drawn Venn diagram (Logic + Machine learning = ILP), for the top of
# the Overview tab.
# ---------------------------------------------------------------------

import math

VENN_COLORS = {
    # same palette as the Home pipeline figure
    "background": "#F3F4F8",
    "blue": "#2F6FBF",
    "blue_fill": "#E3EDF9",
    "red": "#C0613F",
    "red_fill": "#F9E9E2",
    "ink": "#11026D",
    "caption": "#5B6472",
}


def ilp_venn_svg(background: bool = True) -> str:
    c = VENN_COLORS
    font = "Inter,'Source Sans 3','Segoe UI',Helvetica,Arial,sans-serif"
    left = "M 162 568 a 410 410 0 1 0 820 0 a 410 410 0 1 0 -820 0 Z"
    right = "M 621 568 a 414 414 0 1 0 828 0 a 414 414 0 1 0 -828 0 Z"
    rect = f'<rect width="1606" height="1332" fill="{c["background"]}"/>' if background else ""

    def lines(x: int, words: list[str]) -> str:
        return "".join(
            f'<text x="{x}" y="{y}" font-size="54" font-weight="500" fill="{c["ink"]}">{w}</text>'
            for y, w in zip((480, 565, 650), words)
        )

    return f"""<svg viewBox="0 0 1606 1332" xmlns="http://www.w3.org/2000/svg"
  style="width:100%;height:auto;display:block;border-radius:22px;" font-family="{font}">
<defs><clipPath id="ilpVennLeft"><path d="{left}"/></clipPath></defs>
{rect}
<path d="{left}" fill="{c["blue_fill"]}"/>
<path d="{right}" fill="{c["red_fill"]}"/>
<path d="{right}" fill="{c["ink"]}" fill-opacity="0.10" clip-path="url(#ilpVennLeft)"/>
<path d="{left}" fill="none" stroke="{c["blue"]}" stroke-width="7"/>
<path d="{right}" fill="none" stroke="{c["red"]}" stroke-width="7"/>
<text x="415" y="118" text-anchor="middle" font-size="64" font-weight="700" letter-spacing="3" fill="{c["blue"]}">LOGIC</text>
<text x="1190" y="118" text-anchor="middle" font-size="64" font-weight="700" letter-spacing="3" fill="{c["red"]}">MACHINE LEARNING</text>
{lines(235, ["rules", "reasoning", "explainable"])}
{lines(1040, ["examples", "learning", "generalization"])}
<text x="803" y="610" text-anchor="middle" font-size="170" font-weight="800" fill="{c["ink"]}">ILP</text>
<path d="M 152 1040 L 152 1072 Q 152 1090 170 1090 L 770 1090 Q 803 1090 803 1122 Q 803 1090 836 1090 L 1436 1090 Q 1454 1090 1454 1072 L 1454 1040" fill="none" stroke="{c["ink"]}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
<text x="803" y="1230" text-anchor="middle" font-size="62" font-weight="700" letter-spacing="2" fill="{c["ink"]}">An AI that learns... and explains.</text>
</svg>"""


def render_ilp_venn(max_width: str = "100%") -> None:
    """The diagram as an <svg> element (its height follows its width)."""
    st.markdown(
        f'<div style="max-width:{max_width};margin:0 auto;">' + ilp_venn_svg() + "</div>",
        unsafe_allow_html=True,
    )


def render_ilp_venn_background(container_key: str) -> None:
    """The diagram as the *background* of a keyed container, so that it never
    sets the height of its row: the container takes the height of the card next
    to it, and the drawing is scaled to fit (kept centered, ratio preserved).

    Use inside `with st.container(key=container_key):`.
    """
    import base64

    encoded = base64.b64encode(ilp_venn_svg(background=False).encode("utf-8")).decode("ascii")
    key = container_key
    st.markdown(
        f"""
        <style>
        /* The column stays in the row (its height is the height of the card next to
           it); the drawing is laid over the whole column, so it never sets the
           height of the row. */
        div[data-testid="stColumn"]:has(.st-key-{key}),
        div[data-testid="column"]:has(.st-key-{key}) {{
            position: relative !important;
        }}
        div[data-testid="stColumn"]:has(.st-key-{key}) > div[data-testid="stVerticalBlock"]:not([class*="st-key-"]),
        div[data-testid="column"]:has(.st-key-{key}) > div[data-testid="stVerticalBlock"]:not([class*="st-key-"]) {{
            position: static !important;
        }}
        div[class*="st-key-{key}"] {{
            position: absolute !important;
            top: 0 !important; right: 0 !important; bottom: 0 !important; left: 0 !important;
            width: auto !important;
            height: auto !important;
            background: {VENN_COLORS["background"]} url("data:image/svg+xml;base64,{encoded}")
                        center / contain no-repeat !important;
            padding: 0 !important;
            overflow: hidden;
        }}
        /* Columns stacked on a narrow screen: no card next to the drawing, give it a height. */
        @media (max-width: 640px) {{
            div[class*="st-key-{key}"] {{
                position: relative !important;
                height: 280px !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
