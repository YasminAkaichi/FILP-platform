"""The ASP tab of the ILP page: Answer Set Programming in simple words.

Everything interactive here is computed for real, with a tiny solver written
for these examples: the stable-model test (Gelfond & Lifschitz) on the
tea-or-coffee program, the effect of default negation, and the enumeration of
the answer sets of the map-colouring problem.
"""

from __future__ import annotations

from itertools import product

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

COLOR_HEX = {"orange": "#F28C28", "violet": "#7C5CC4", "green": "#3FA672"}


# ---------------------------------------------------------------------
# A tiny solver for ground normal programs
# rule = (head, positive_body, negative_body)
# ---------------------------------------------------------------------

def least_model(definite_rules: list[tuple[str, tuple[str, ...]]]) -> set[str]:
    model: set[str] = set()
    changed = True
    while changed:
        changed = False
        for head, body in definite_rules:
            if head not in model and all(atom in model for atom in body):
                model.add(head)
                changed = True
    return model


def reduct(program, candidate: set[str]):
    """Gelfond-Lifschitz reduct: drop the rules blocked by the candidate world,
    erase the remaining 'not' literals."""
    crossed, kept = [], []
    for head, positive, negative in program:
        if set(negative) & candidate:
            crossed.append((head, positive, negative))
        else:
            kept.append((head, positive))
    return crossed, kept


def stable_models(program, atoms: list[str]) -> list[set[str]]:
    models = []
    for bits in product([False, True], repeat=len(atoms)):
        candidate = {atom for atom, bit in zip(atoms, bits) if bit}
        _, kept = reduct(program, candidate)
        if least_model(kept) == candidate:
            models.append(candidate)
    return models


def show_rule(rule) -> str:
    head, positive, negative = rule
    body = list(positive) + [f"not {atom}" for atom in negative]
    return f"{head} :- {', '.join(body)}." if body else f"{head}."


def show_world(world: set[str]) -> str:
    return "{" + ", ".join(sorted(world)) + "}" if world else "{ }"


# ---------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------

def _css() -> None:
    st.markdown(
        f"""
        <style>
        .asp-hero {{
            border: 1px solid {PALETTE["border"]};
            background: {PALETTE["bg_card"]};
            border-radius: 18px;
            padding: 28px 32px;
            margin-bottom: 8px;
        }}
        .asp-hero h2 {{ margin: 0 0 6px 0; font-size: 1.9rem; color: {PALETTE["primary"]}; }}
        .asp-hero p {{ margin: 0; font-size: 1.05rem; color: {PALETTE["text_muted"]}; }}
        .asp-kicker {{
            font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase;
            color: {PALETTE["text_muted"]}; font-weight: 700; margin-top: 34px; margin-bottom: 2px;
        }}
        .asp-title {{ font-size: 1.45rem; font-weight: 700; color: {PALETTE["primary"]}; margin: 0 0 6px 0; }}
        .asp-lead {{ color: {PALETTE["text_muted"]}; font-size: 1rem; margin-bottom: 14px; }}
        .asp-card {{
            border: 1px solid {PALETTE["border"]}; background: #FFFFFF;
            border-radius: 14px; padding: 18px 20px; height: 100%;
        }}
        .asp-card h4 {{ margin: 0 0 6px 0; font-size: 1.02rem; color: {PALETTE["primary"]}; }}
        .asp-card p, .asp-card li {{ color: {PALETTE["text"]}; font-size: 0.96rem; }}
        .asp-note {{
            border-left: 4px solid {PALETTE["primary"]}; background: {PALETTE["bg_card"]};
            border-radius: 0 12px 12px 0; padding: 12px 16px; color: {PALETTE["text"]}; margin-top: 12px;
        }}
        .asp-verdict {{ border-radius: 12px; padding: 12px 16px; font-size: 0.97rem; margin-top: 10px; }}
        .asp-verdict.ok {{ background: {PALETTE["ok_soft"]}; color: {PALETTE["ok"]}; }}
        .asp-verdict.bad {{ background: {PALETTE["bad_soft"]}; color: {PALETTE["bad"]}; }}
        .asp-flow {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin: 10px 0 6px 0; }}
        .asp-chip {{
            border: 1px solid {PALETTE["border"]}; background: {PALETTE["bg_card"]};
            border-radius: 999px; padding: 5px 13px; color: {PALETTE["text"]}; font-size: 0.95rem;
        }}
        .asp-chip.dark {{ background: {PALETTE["primary"]}; border-color: {PALETTE["primary"]}; color: #FFFFFF; }}
        table.asp-table {{ width: 100%; border-collapse: collapse; font-size: 0.95rem; }}
        table.asp-table th {{
            text-align: left; color: {PALETTE["text_muted"]}; font-weight: 600;
            border-bottom: 1px solid {PALETTE["border"]}; padding: 8px 10px;
        }}
        table.asp-table td {{ border-bottom: 1px solid {PALETTE["border"]}; padding: 8px 10px; color: {PALETTE["text"]}; }}
        .asp-world {{
            display: inline-flex; gap: 6px; align-items: center; margin: 0 14px 10px 0;
            border: 1px solid {PALETTE["border"]}; border-radius: 12px; padding: 8px 10px; background: #FFFFFF;
        }}
        .asp-world .sq {{ width: 26px; height: 26px; border-radius: 6px; display: inline-block; }}
        .asp-world .lbl {{ font-size: 0.8rem; color: {PALETTE["text_muted"]}; margin-right: 4px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _section(kicker: str, title: str, lead: str = "") -> None:
    st.markdown(f'<div class="asp-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="asp-title">{title}</div>', unsafe_allow_html=True)
    if lead:
        st.markdown(f'<div class="asp-lead">{lead}</div>', unsafe_allow_html=True)


def _note(html: str) -> None:
    st.markdown(f'<div class="asp-note">{html}</div>', unsafe_allow_html=True)


def render_asp() -> None:
    _css()

    st.markdown(
        """
        <div class="asp-hero">
          <h2>Answer Set Programming (ASP)</h2>
          <p>When the computer imagines <b>all</b> the possible worlds. Answer sets, stable models,
          and how it differs from Prolog.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- 1. What is ASP --------------------------------------------------
    _section(
        "Step 1",
        "What is ASP?",
        "You describe the <b>problem</b>: facts, rules, constraints. The computer gives you <b>all</b> the solutions.",
    )
    c1, c2, c3 = st.columns(3, gap="small")
    for column, text in zip((c1, c2, c3), ("World 1", "World 2", "World 3")):
        with column:
            st.markdown(
                f'<div class="asp-card"><h4>{text}</h4><p>A coherent set of facts that respects every rule.</p></div>',
                unsafe_allow_html=True,
            )
    _note(
        "Each solution is an <b>answer set</b>, a possible world that is consistent with your rules. "
        "You ask no question: you receive worlds."
    )

    # ---- 2. Prolog vs ASP ------------------------------------------------
    _section("Step 2", "Prolog or ASP?", "Same family, two ways of thinking.")
    p1, p2 = st.columns(2, gap="medium")
    with p1:
        st.markdown(
            """
            <div class="asp-card"><h4>Prolog is a detective</h4>
            <p>You ask <b>one</b> question. It follows <b>one</b> trail, step by step, until a proof.</p>
            <p style="color:#5B6472;">“Is it true?”</p></div>
            """,
            unsafe_allow_html=True,
        )
    with p2:
        st.markdown(
            """
            <div class="asp-card"><h4>ASP is an architect</h4>
            <p>You give the constraints. It draws <b>all</b> the plans that respect them.</p>
            <p style="color:#5B6472;">“What is possible?”</p></div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <table class="asp-table" style="margin-top:14px;">
          <tr><th></th><th>Prolog</th><th>ASP</th></tr>
          <tr><td>You give it</td><td>a question</td><td>a problem</td></tr>
          <tr><td>It looks for</td><td>one proof, from the top down</td><td>all the worlds, from the bottom up</td></tr>
          <tr><td>Order of the rules</td><td>matters</td><td>does not matter</td></tr>
          <tr><td>Infinite loop?</td><td>possible</td><td>no (on a finite problem)</td></tr>
          <tr><td>The “not”</td><td>procedural (<code>\\+</code>)</td><td>logical (stable models)</td></tr>
          <tr><td>Tool</td><td>SWI-Prolog</td><td>clingo</td></tr>
        </table>
        """,
        unsafe_allow_html=True,
    )
    _note("<b>Prolog deduces. ASP searches for all the solutions.</b>")

    # ---- 3. The "not" -----------------------------------------------------
    _section(
        "Step 3",
        "The star of ASP: the “not”",
        "Negation by default: <code>not x</code> means “I have no reason to believe x”.",
    )
    st.code("go_out :- not rain.", language="prolog")
    add_rain = st.toggle("Add the fact  rain.", key="asp_add_rain")
    rain_program = [("go_out", (), ("rain",))]
    if add_rain:
        rain_program.append(("rain", (), ()))
    rain_models = stable_models(rain_program, ["rain", "go_out"])
    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown("**The program**")
        st.code("\n".join(show_rule(rule) for rule in rain_program), language="prolog")
    with right:
        st.markdown("**The answer set**")
        st.code(show_world(rain_models[0]) if rain_models else "no answer set", language="prolog")
    if add_rain:
        st.markdown(
            '<div class="asp-verdict bad">Now we know it rains: <code>go_out</code> is no longer concluded. '
            "Adding information <b>removed</b> a conclusion.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="asp-verdict ok">Nothing is known about the rain, so <code>go_out</code> holds: '
            "I go out, <i>unless</i> I know that it rains.</div>",
            unsafe_allow_html=True,
        )
    _note(
        "Adding information can <b>remove</b> a conclusion: this is called <b>non-monotonic</b> reasoning. "
        "It is what makes ASP natural for common-sense rules and exceptions."
    )

    # ---- 4. Tea or coffee -------------------------------------------------
    _section(
        "Step 4",
        "Tea or coffee?",
        "The example that explains everything: <i>I have tea if I do not have coffee, and the other way round.</i>",
    )
    tea_program = [("tea", (), ("coffee",)), ("coffee", (), ("tea",))]
    st.code("\n".join(show_rule(rule) for rule in tea_program), language="prolog")
    tea_models = stable_models(tea_program, ["tea", "coffee"])
    st.markdown(
        '<div class="asp-flow">'
        + "".join(f'<span class="asp-chip dark">world {i + 1}: {show_world(m)}</span>' for i, m in enumerate(tea_models))
        + "</div>",
        unsafe_allow_html=True,
    )
    _note(
        f"<b>{len(tea_models)} answer sets.</b> Neither is “the right one”: both are coherent worlds. "
        "With no answer set, the problem is impossible; with several, there are several solutions."
    )

    # ---- 5. Stable model test ---------------------------------------------
    _section(
        "Step 5",
        "What is a stable model?",
        "Guess a world, then check that it <b>justifies itself</b>. Pick a world to test on the tea-or-coffee program.",
    )
    steps = st.columns(4, gap="small")
    step_texts = (
        "1. Guess a world.",
        "2. Cross out the rules <code>not x</code> when x is in this world.",
        "3. Erase the remaining <code>not</code>, then deduce.",
        "4. Do you get your world back? Then it is <b>stable</b>.",
    )
    for column, text in zip(steps, step_texts):
        with column:
            st.markdown(f'<div class="asp-card"><p style="margin:0;">{text}</p></div>', unsafe_allow_html=True)

    guesses = {"{ }": set(), "{tea}": {"tea"}, "{coffee}": {"coffee"}, "{tea, coffee}": {"tea", "coffee"}}
    guess_label = st.radio(
        "World to test",
        options=list(guesses),
        index=1,
        horizontal=True,
        key="asp_guess",
    )
    guess = guesses[guess_label]
    crossed, kept = reduct(tea_program, guess)
    deduced = least_model(kept)
    stable = deduced == guess

    g1, g2, g3 = st.columns(3, gap="small")
    with g1:
        st.markdown("**Rules crossed out**")
        st.code("\n".join(show_rule(r) for r in crossed) or "(none)", language="prolog")
    with g2:
        st.markdown("**Rules left, without “not”**")
        st.code("\n".join(f"{h}." if not b else f"{h} :- {', '.join(b)}." for h, b in kept) or "(none)", language="prolog")
    with g3:
        st.markdown("**What we deduce**")
        st.code(show_world(deduced), language="prolog")

    st.markdown(
        f'<div class="asp-verdict {"ok" if stable else "bad"}">'
        f"We guessed {show_world(guess)} and we get {show_world(deduced)}: "
        f'{"the world retrieves itself, it is stable." if stable else "not the same world, so it is not stable."}'
        "</div>",
        unsafe_allow_html=True,
    )
    _note(
        "<b>Answer set = stable model.</b> A set of facts that respects all the rules and constraints, "
        "contains <b>nothing without a justification</b>, and passes this test. Like a story where every event "
        "has its cause… in the story itself. "
        "<span style='color:#5B6472;'>(Stable-model semantics: Gelfond &amp; Lifschitz, 1988.)</span>"
    )

    # ---- 6. Map colouring -------------------------------------------------
    _section(
        "Step 6",
        "Example: colouring a map",
        "Regions side by side, a few pencils. Each region gets <b>exactly one</b> colour, and two neighbours never share one.",
    )
    ctrl1, ctrl2 = st.columns([1, 1.4], gap="large")
    with ctrl1:
        n_regions = st.slider("Number of regions", 2, 5, 3, key="asp_regions")
    with ctrl2:
        colors = st.multiselect(
            "Pencils", options=list(COLOR_HEX), default=["orange", "violet"], key="asp_colors"
        )

    regions = [chr(ord("a") + i) for i in range(n_regions)]
    neighbours = list(zip(regions, regions[1:]))
    answer_sets = []
    if colors:
        for assignment in product(colors, repeat=n_regions):
            if all(assignment[i] != assignment[i + 1] for i in range(n_regions - 1)):
                answer_sets.append(assignment)

    code_left, code_right = st.columns(2, gap="large")
    with code_left:
        st.markdown("**1. The facts**")
        st.code(
            " ".join(f"region({r})." for r in regions)
            + "\n"
            + " ".join(f"neighbour({x},{y})." for x, y in neighbours)
            + "\n"
            + " ".join(f"colour({c})." for c in colors),
            language="prolog",
        )
        st.markdown("**2. Generate: each region picks one colour**")
        st.code("{ paint(R,C) : colour(C) } = 1 :- region(R).", language="prolog")
    with code_right:
        st.markdown("**3. Test: forbid the bad colourings**")
        st.code(":- neighbour(X,Y), paint(X,C), paint(Y,C).", language="prolog")
        st.markdown(
            "A rule **without a head** is a **constraint**: “this case must NEVER happen”. "
            "We write **no search algorithm**: the solver does it."
        )

    status = (
        f"SATISFIABLE · Models: {len(answer_sets)}" if answer_sets else "UNSATISFIABLE · Models: 0"
    )
    st.markdown(
        f'<div class="asp-verdict {"ok" if answer_sets else "bad"}"><b>{status}</b></div>',
        unsafe_allow_html=True,
    )

    shown = answer_sets[:8]
    worlds_html = ""
    for index, assignment in enumerate(shown, start=1):
        squares = "".join(
            f'<span class="sq" title="{region}: {color}" style="background:{COLOR_HEX[color]};"></span>'
            for region, color in zip(regions, assignment)
        )
        worlds_html += f'<span class="asp-world"><span class="lbl">Answer {index}</span>{squares}</span>'
    if worlds_html:
        st.markdown(worlds_html, unsafe_allow_html=True)
        if len(answer_sets) > len(shown):
            st.caption(f"{len(shown)} of {len(answer_sets)} answer sets shown. Regions are in order: " + ", ".join(regions) + ".")
        else:
            st.caption("Regions are in order: " + ", ".join(regions) + ".")
    _note(
        "“Region a orange, region b orange”? Eliminated by the constraint: it is never proposed. "
        "Add a colour or a region and the answer sets are recomputed, without changing your method."
    )

    # ---- 7. Uses ----------------------------------------------------------
    _section(
        "Step 7",
        "What is it used for?",
        "What these problems have in common: many choices plus constraints, a combinatorial problem.",
    )
    uses = [
        ("Timetables", "Courses, rooms, teachers… with no conflict."),
        ("Sudoku and puzzles", "One cell = one choice, one rule = one constraint."),
        ("Planning", "Robots, logistics, missions."),
        ("Configuration", "Assembling parts that are compatible with each other."),
        ("Bioinformatics", "Networks of genes and proteins."),
        ("Diagnosis", "Listing all the possible faults."),
    ]
    for row in (uses[:3], uses[3:]):
        for column, (title, text) in zip(st.columns(3, gap="small"), row):
            with column:
                st.markdown(f'<div class="asp-card"><h4>{title}</h4><p>{text}</p></div>', unsafe_allow_html=True)
        st.write("")
    _note(
        "<b>The star tool: clingo</b> (Potassco project). It <i>grounds</i> the variables, then <i>solves</i>."
    )

    # ---- 8. ASP and ILP ---------------------------------------------------
    _section(
        "In this platform",
        "ASP and ILP",
        "Popper, the ILP system behind most approaches of this platform, is built on ASP.",
    )
    st.markdown(
        """
        <div class="asp-card">
          <p style="margin:0;">Popper describes the space of possible programs (the <b>language bias</b>) as an ASP
          program, and asks <b>clingo</b> for an answer set: each answer set is one <b>candidate hypothesis</b>.
          When a candidate fails on the examples, Popper adds <b>constraints</b> to the ASP program, so that the
          programs that would fail for the same reason are never proposed again. This is the
          <i>generate, test and constrain</i> loop that the federated approaches of this platform distribute
          across clients.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="asp-note">Ready to see it run? Open the <b>Learning</b> tab, pick Popper, and run it on a dataset.</div>',
        unsafe_allow_html=True,
    )
