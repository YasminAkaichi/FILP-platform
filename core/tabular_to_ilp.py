"""Convert a tabular dataset (one row per sample, one column per feature)
into an ILP-ready dataset, for both Popper (bias.pl/bk.pl/exs.pl) and
Andante (a single native .pl file).

Design
------
Each row of the DataFrame is treated as one "sample" (e.g. a patient).
Each feature column becomes its own Prolog predicate describing that
sample:

  * A boolean-like column (yes/no, oui/non, true/false, 1/0, with at
    most 2 distinct values) becomes a unary predicate, following the
    usual closed-world convention: a fact is emitted only for samples
    where the value is "truthy" (e.g. `fever(p3).`), and simply absent
    otherwise.
  * Any other column (categorical or numeric) becomes a binary predicate
    `col(sample_id, value).`, with one fact per row.

The user picks one column as the learning target and one value from it
that counts as "positive" — every other value becomes a negative
example of the target predicate (arity 1, one argument: the sample id).

A free-text "background knowledge" box lets the user add simple rules in
natural language ("if X and Y then Z" / "si X et Y alors Z"), which are
matched (by keyword / substring, not an LLM — see parse_background_text)
against the already-known predicate names and turned into extra Prolog
background clauses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

TRUTHY_TOKENS = {"yes", "oui", "true", "vrai", "1", "y", "o"}
FALSY_TOKENS = {"no", "non", "false", "faux", "0", "n"}
BOOLEAN_TOKENS = TRUTHY_TOKENS | FALSY_TOKENS


def sanitize_identifier(text: str, fallback: str = "x") -> str:
    """Turn arbitrary text into a valid lowercase Prolog atom/functor name."""
    text = str(text).strip().lower()
    text = text.replace(" ", "_").replace("-", "_")
    text = re.sub(r"[^a-z0-9_]", "", text)
    text = re.sub(r"_+", "_", text).strip("_")
    if not text or not text[0].isalpha():
        text = f"{fallback}_{text}" if text else fallback
    return text


def sanitize_atom_value(value) -> str:
    """Turn a cell value into a valid Prolog constant (atom or number)."""
    if pd.isna(value):
        return "unknown"
    # pandas/numpy scalars (e.g. numpy.int64, numpy.float64) are NOT
    # instances of Python's own int/float, so isinstance() checks below
    # would silently miss them and fall through to the generic
    # identifier-sanitizing branch (e.g. turning 45 into "v_45" instead
    # of "45"). .item() normalizes any numpy scalar to a native Python
    # type; plain Python values don't have .item() so they pass through.
    value = getattr(value, "item", lambda: value)()
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int,)):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value).replace("-", "neg_")
    return sanitize_identifier(value, fallback="v")


def is_boolean_like(series: pd.Series) -> bool:
    values = {str(v).strip().lower() for v in series.dropna().unique()}
    if not values:
        return False
    return values.issubset(BOOLEAN_TOKENS)


def is_truthy(value) -> bool:
    return str(value).strip().lower() in TRUTHY_TOKENS


CONTINUOUS_UNIQUE_THRESHOLD = 10
DEFAULT_THRESHOLD_QUANTILES = (0.25, 0.5, 0.75)


def is_continuous_numeric(series: pd.Series, unique_threshold: int = CONTINUOUS_UNIQUE_THRESHOLD) -> bool:
    """A numeric column with more distinct values than `unique_threshold`
    is treated as continuous. Left as a `col(sample, value)` predicate,
    almost every value is unique to one sample, so no clause can ever
    generalize across samples (Popper/Andante can't unify two different
    constants) — the learner silently finds nothing to learn. Binarizing
    around a handful of quantile cut points turns it into predicates
    that are actually shared across many samples, which is learnable.
    """
    if not pd.api.types.is_numeric_dtype(series):
        return False
    return series.dropna().nunique() > unique_threshold


def compute_thresholds(
    series: pd.Series, quantiles: tuple[float, ...] = DEFAULT_THRESHOLD_QUANTILES
) -> list[float]:
    """Cut points for binarizing a continuous column, one per quantile.

    Rather than a single median split (one bit of information per
    column), this gives the learner several candidate cut points — e.g.
    quartiles — so it can pick whichever one actually separates the
    classes, much like `above_clump_thickness_4/6/8` in a hand-built
    bias file. Values are deduplicated (a low-cardinality-but-still
    "continuous" column can have repeated quantiles) and sorted.
    """
    values = series.dropna()
    cuts = sorted({round(float(values.quantile(q)), 4) for q in quantiles})
    return cuts


def format_threshold_for_name(value: float) -> str:
    """Turn a numeric threshold into a valid Prolog-identifier fragment,
    e.g. 4.5 -> "4_5", -3 -> "neg_3", 4.0 -> "4"."""
    if float(value).is_integer():
        text = str(int(value))
    else:
        text = str(value)
    return text.replace("-", "neg_").replace(".", "_")


@dataclass
class ColumnPlan:
    """Describes how one feature column will be turned into a predicate."""

    original_name: str
    predicate: str
    kind: str  # "boolean" or "valued"
    value_type: str = ""  # only used for "valued" columns
    threshold: float | None = None  # set only for quantile-binarized continuous columns (>= threshold)


@dataclass
class ConversionPlan:
    id_column: str | None
    sample_ids: list[str]
    feature_plans: list[ColumnPlan]
    target_predicate: str
    positive_ids: set[str] = field(default_factory=set)
    negative_ids: set[str] = field(default_factory=set)


def pick_id_column(df: pd.DataFrame, exclude: set[str]) -> str | None:
    for col in df.columns:
        if col in exclude:
            continue
        name = str(col).strip().lower()
        if name in {"id", "patient", "patient_id", "sample", "sample_id", "name"}:
            return col
    return None


def build_conversion_plan(
    df: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    positive_values: list[str],
) -> tuple[ConversionPlan, pd.DataFrame]:
    """Compute sample ids and per-column predicate plans.

    Returns the plan plus a working copy of the dataframe indexed by the
    generated/derived sample id (as a sanitized string), so callers can
    iterate `df.iterrows()` and know each row's sample id via the index.
    """
    id_column = pick_id_column(df, exclude={target_column, *feature_columns} - {target_column})
    work = df.copy()

    if id_column is not None:
        raw_ids = work[id_column].astype(str)
        seen: dict[str, int] = {}
        sample_ids = []
        for raw in raw_ids:
            base = sanitize_identifier(raw, fallback="s")
            n = seen.get(base, 0)
            seen[base] = n + 1
            sample_ids.append(base if n == 0 else f"{base}_{n}")
    else:
        sample_ids = [f"p{i+1}" for i in range(len(work))]

    work.index = sample_ids

    plans: list[ColumnPlan] = []
    for col in feature_columns:
        if col == target_column or col == id_column:
            continue
        predicate = sanitize_identifier(col, fallback="feature")
        if is_boolean_like(df[col]):
            plans.append(ColumnPlan(original_name=col, predicate=predicate, kind="boolean"))
        elif is_continuous_numeric(df[col]):
            # Multi-threshold binarize: above_<col>_<cut>(sample) iff
            # value >= cut, one predicate per quantile cut point (by
            # default quartiles). A single median split only gives the
            # learner one candidate cut point per column; several
            # thresholds let it pick whichever one actually separates
            # the classes, the same idea as a hand-built bias file's
            # above_feature_4/6/8-style predicates.
            for cut in compute_thresholds(df[col]):
                plans.append(
                    ColumnPlan(
                        original_name=col,
                        predicate=f"above_{predicate}_{format_threshold_for_name(cut)}",
                        kind="boolean",
                        threshold=cut,
                    )
                )
        else:
            plans.append(
                ColumnPlan(
                    original_name=col,
                    predicate=predicate,
                    kind="valued",
                    value_type=f"val_{predicate}",
                )
            )

    target_predicate = sanitize_identifier(target_column, fallback="target")
    positive_norm = {str(v).strip().lower() for v in positive_values}

    positive_ids: set[str] = set()
    negative_ids: set[str] = set()
    for sid, value in zip(sample_ids, df[target_column]):
        if str(value).strip().lower() in positive_norm:
            positive_ids.add(sid)
        else:
            negative_ids.add(sid)

    plan = ConversionPlan(
        id_column=id_column,
        sample_ids=sample_ids,
        feature_plans=plans,
        target_predicate=target_predicate,
        positive_ids=positive_ids,
        negative_ids=negative_ids,
    )
    return plan, work


def generate_feature_facts(plan: ConversionPlan, work: pd.DataFrame) -> list[str]:
    """One fact per (sample, feature) pair, following the boolean/valued
    convention described in the module docstring.

    Iterates each column as a pandas Series (fast, vectorized-ish) rather
    than doing one scalar work.loc[sid, col] lookup per (row, column) —
    for a wide table (many feature columns) the per-lookup overhead of
    .loc adds up fast (e.g. ~17k individual lookups for a 569-row,
    30-column table), and this function runs twice per Streamlit rerun
    (once for the Popper preview, once for Andante), so the old version
    could noticeably stall the UI on every widget interaction.
    """
    facts: list[str] = []
    for col_plan in plan.feature_plans:
        series = work[col_plan.original_name]
        if col_plan.kind == "boolean":
            if col_plan.threshold is not None:
                for sid, value in series.items():
                    if pd.notna(value) and float(value) >= col_plan.threshold:
                        facts.append(f"{col_plan.predicate}({sid}).")
            else:
                for sid, value in series.items():
                    if pd.notna(value) and is_truthy(value):
                        facts.append(f"{col_plan.predicate}({sid}).")
        else:
            for sid, value in series.items():
                if pd.notna(value):
                    facts.append(f"{col_plan.predicate}({sid}, {sanitize_atom_value(value)}).")
    return facts


# ---------------------------------------------------------------------
# Free-text background knowledge -> Prolog rules (simple keyword parser)
# ---------------------------------------------------------------------

_IF_THEN_PATTERNS = [
    # English: "if X and Y then Z"
    re.compile(r"^\s*if\s+(?P<cond>.+?)\s+then\s+(?P<concl>.+?)\s*\.?\s*$", re.IGNORECASE),
    # French: "si X et Y alors Z"
    re.compile(r"^\s*si\s+(?P<cond>.+?)\s+alors\s+(?P<concl>.+?)\s*\.?\s*$", re.IGNORECASE),
]
_AND_SPLIT = re.compile(r"\s*(?:,|\band\b|\bet\b)\s*", re.IGNORECASE)


def _match_known_predicate(phrase: str, known: dict[str, str]) -> str | None:
    """Best-effort match of a free-text phrase to a known predicate name.

    `known` maps a normalized (sanitized, underscore-joined) token to the
    real predicate name. We try an exact match first, then a substring
    match in both directions, so e.g. "high fever" matches "fever" and
    "fever" matches a column literally named "high_fever".
    """
    token = sanitize_identifier(phrase, fallback="")
    if not token:
        return None
    if token in known:
        return known[token]
    for norm, pred in known.items():
        if token in norm or norm in token:
            return pred
    return None


def parse_background_text(text: str, known_predicates: list[str]) -> tuple[list[str], list[str]]:
    """Parse free-text domain rules into Prolog clauses.

    Returns (rules, warnings): `rules` are ready-to-append Prolog clause
    strings (arity-1, over a shared sample-id variable), `warnings`
    lists lines that couldn't be matched to any known predicate so the
    UI can flag them instead of silently dropping them.
    """
    known = {sanitize_identifier(p): p for p in known_predicates}
    rules: list[str] = []
    warnings: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        matched = None
        for pattern in _IF_THEN_PATTERNS:
            m = pattern.match(line)
            if m:
                matched = m
                break

        if matched is None:
            warnings.append(f"Not recognized (expected \"if ... then ...\" / \"si ... alors ...\"): {line}")
            continue

        cond_phrases = [p for p in _AND_SPLIT.split(matched.group("cond")) if p.strip()]
        concl_phrase = matched.group("concl")

        cond_preds = [_match_known_predicate(p, known) for p in cond_phrases]
        concl_pred = _match_known_predicate(concl_phrase, known)

        if concl_pred is None or any(p is None for p in cond_preds):
            unresolved = [
                phrase
                for phrase, pred in zip([*cond_phrases, concl_phrase], [*cond_preds, concl_pred])
                if pred is None
            ]
            warnings.append(
                f"Couldn't match to a known column/predicate ({', '.join(unresolved)}): {line}"
            )
            continue

        body = ", ".join(f"{p}(S)" for p in cond_preds)
        rules.append(f"{concl_pred}(S) :- {body}.")

    return rules, warnings


# ---------------------------------------------------------------------
# Popper output (bias.pl / bk.pl / exs.pl)
# ---------------------------------------------------------------------


def build_popper_dataset(
    plan: ConversionPlan,
    work: pd.DataFrame,
    background_rules: list[str] | None = None,
) -> dict[str, str]:
    background_rules = background_rules or []

    # max_vars stays small on purpose: every body predicate here only
    # ever takes the sample-id variable as input (arity 1, or arity 2 for
    # the rare non-numeric multi-category column, whose 2nd argument is
    # a distinct, non-shared value variable) — none of them introduce a
    # NEW id-typed variable, so a clause never needs more than a couple
    # of variables regardless of how many feature predicates exist. This
    # also keeps Popper's search space from exploding as more
    # multi-threshold predicates get generated for wide tables.
    bias_lines = [
        f"% Auto-generated from an uploaded table — {len(plan.sample_ids)} samples,",
        f"% {len(plan.feature_plans)} feature predicates, target = {plan.target_predicate}/1.",
        "",
        "max_clauses(4).",
        "max_vars(4).",
        "max_body(4).",
        "",
        f"head_pred({plan.target_predicate},1).",
    ]
    for col_plan in plan.feature_plans:
        arity = 1 if col_plan.kind == "boolean" else 2
        bias_lines.append(f"body_pred({col_plan.predicate},{arity}).")
    bias_lines.append("")
    bias_lines.append(f"type({plan.target_predicate},(id,)).")
    for col_plan in plan.feature_plans:
        if col_plan.kind == "boolean":
            bias_lines.append(f"type({col_plan.predicate},(id,)).")
        else:
            bias_lines.append(f"type({col_plan.predicate},(id,{col_plan.value_type})).")
    bias_lines.append("")
    bias_lines.append("% directions specify which arguments are input and which are output")
    bias_lines.append(f"direction({plan.target_predicate},(in,)).")
    for col_plan in plan.feature_plans:
        if col_plan.kind == "boolean":
            bias_lines.append(f"direction({col_plan.predicate},(in,)).")
        else:
            bias_lines.append(f"direction({col_plan.predicate},(in,out)).")

    bias_lines.append("")
    bias_lines.append(
        "% Every literal in a clause describes the SAME sample — without this,"
    )
    bias_lines.append(
        "% Popper could combine facts about two different samples in one clause,"
    )
    bias_lines.append("% which is never meaningful here (each id is an independent row).")
    bias_lines.append(":-")
    bias_lines.append("    clause(C),")
    bias_lines.append("    #count{V : var_type(C,V,id)} != 1.")

    bk_lines = [":-style_check(-discontiguous).", ""]
    bk_lines.extend(generate_feature_facts(plan, work))
    if background_rules:
        bk_lines.append("")
        bk_lines.append("% Background knowledge added from the free-text box")
        bk_lines.extend(background_rules)

    exs_lines = []
    for sid in sorted(plan.positive_ids):
        exs_lines.append(f"pos({plan.target_predicate}({sid})).")
    exs_lines.append("")
    for sid in sorted(plan.negative_ids):
        exs_lines.append(f"neg({plan.target_predicate}({sid})).")

    return {
        "bias.pl": "\n".join(bias_lines) + "\n",
        "bk.pl": "\n".join(bk_lines) + "\n",
        "exs.pl": "\n".join(exs_lines) + "\n",
    }


# ---------------------------------------------------------------------
# Andante output (single native .pl file)
# ---------------------------------------------------------------------


def build_andante_dataset(
    plan: ConversionPlan,
    work: pd.DataFrame,
    background_rules: list[str] | None = None,
) -> str:
    background_rules = background_rules or []

    lines = [
        "set(verbose,0).",
        "set(max_search_states,5000).",
        "",
        f"modeh(1,{plan.target_predicate}(+id)).",
    ]
    for col_plan in plan.feature_plans:
        if col_plan.kind == "boolean":
            lines.append(f"modeb(*,{col_plan.predicate}(+id)).")
        else:
            lines.append(f"modeb(*,{col_plan.predicate}(+id,-{col_plan.value_type})).")

    lines.append("")
    for col_plan in plan.feature_plans:
        arity = 1 if col_plan.kind == "boolean" else 2
        lines.append(f"determination({plan.target_predicate}/1,{col_plan.predicate}/{arity}).")

    lines.append("")
    lines.append(":- begin_bg.")
    lines.append("")
    lines.extend(generate_feature_facts(plan, work))
    if background_rules:
        lines.append("")
        lines.append("% Background knowledge added from the free-text box")
        lines.extend(background_rules)
    lines.append("")
    lines.append(":- end_bg.")

    lines.append("")
    lines.append(":- begin_in_pos.")
    lines.append("")
    for sid in sorted(plan.positive_ids):
        lines.append(f"{plan.target_predicate}({sid}).")
    lines.append("")
    lines.append(":- end_in_pos.")

    lines.append("")
    lines.append(":- begin_in_neg.")
    lines.append("")
    for sid in sorted(plan.negative_ids):
        lines.append(f"{plan.target_predicate}({sid}).")
    lines.append("")
    lines.append(":- end_in_neg.")

    return "\n".join(lines) + "\n"
