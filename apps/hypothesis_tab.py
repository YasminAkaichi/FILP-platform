"""Hypotheses tab of the Experiments page (Coordination and Collaboration, hybrid evaluation).

Shows, round by round, the program tested by the federated search (what each
client answered, then the aggregated answer) next to the program tested by
"Client 0 (centralized)": the same search, but tested by ONE client holding the
whole dataset. It makes visible where, and why, the two searches part.

Data: hypothesis_log.json written by the Coordination server in the folder of
each experiment (it has the answer of every client); if the file is gone, the
hypothesis_log table of the database is used (aggregated answers only).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from database.connection import get_connection

ROOT = Path(__file__).resolve().parents[1]


def _runs(benchmark_id: int) -> dict[int, int]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT run_number, experiment_id FROM benchmark_runs "
            "WHERE benchmark_id = ? ORDER BY run_number",
            (benchmark_id,),
        ).fetchall()
    return {int(r["run_number"]): int(r["experiment_id"]) for r in rows}


def _twin_benchmark(federated_id: int) -> int | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM benchmarks WHERE name LIKE ? ORDER BY id DESC LIMIT 1",
            (f"Centralized testing, whole % same seed as #{federated_id}",),
        ).fetchone()
    return int(row["id"]) if row else None


def _load_log(experiment_id: int) -> list[dict]:
    path = ROOT / "artifacts" / f"experiment_{experiment_id}" / "hypothesis_log.json"
    if path.is_file():
        try:
            entries = json.loads(path.read_text(encoding="utf-8"))
            return [e for e in entries if not e.get("is_final_validation")]
        except (OSError, ValueError):
            pass
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT sequence_number, hypothesis, score, epsilon_positive, epsilon_negative "
            "FROM hypothesis_log WHERE experiment_id = ? AND is_final_validation = 0 "
            "ORDER BY sequence_number",
            (experiment_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def _program(text: str) -> str:
    return " ; ".join(line.strip() for line in str(text).splitlines() if line.strip())


def _same_program(a: str, b: str) -> bool:
    key = lambda t: sorted(line.strip() for line in str(t).splitlines() if line.strip())
    return key(a) == key(b)


def _outcome(positive, negative) -> str:
    if positive is None or negative is None:
        return "—"
    return f"{str(positive).upper()} / {str(negative).upper()}"


def build_table(federated: list[dict], central: list[dict]) -> pd.DataFrame:
    """One row per round: the federated program with the answer of each client
    and the aggregated answer, then the program of client 0 and its answer."""
    n_clients = max(
        (len(e.get("client_outcomes") or []) for e in federated), default=0
    )
    rows = []
    diverged = False
    for index in range(max(len(federated), len(central))):
        fed = federated[index] if index < len(federated) else None
        cen = central[index] if index < len(central) else None

        row: dict = {"Round": index + 1}
        row["Federated — program"] = _program(fed["hypothesis"]) if fed else "—"
        per_client = {c["client"]: c for c in (fed.get("client_outcomes") or [])} if fed else {}
        for client in range(1, n_clients + 1):
            c = per_client.get(client)
            row[f"Client {client}"] = (
                f"{_outcome(c['epsilon_positive'], c['epsilon_negative'])}  ({c['score']:g})"
                if c
                else "—"
            )
        row["Federated — aggregated"] = (
            _outcome(fed["epsilon_positive"], fed["epsilon_negative"]) if fed else "—"
        )
        row["Federated — score"] = fed["score"] if fed else None
        row["Client 0 — program"] = _program(cen["hypothesis"]) if cen else "—"
        row["Client 0 — outcome"] = (
            _outcome(cen["epsilon_positive"], cen["epsilon_negative"]) if cen else "—"
        )
        row["Client 0 — score"] = cen["score"] if cen else None

        if fed is None or cen is None:
            status = "only one search"
            diverged = True
        elif diverged:
            status = "searches already apart"
        elif not _same_program(fed["hypothesis"], cen["hypothesis"]):
            status = "FIRST DIFFERENT PROGRAM"
            diverged = True
        elif (fed["epsilon_positive"], fed["epsilon_negative"]) != (
            cen["epsilon_positive"],
            cen["epsilon_negative"],
        ) or abs(float(fed["score"]) - float(cen["score"])) > 1e-9:
            status = "same program, DIFFERENT answer"
        else:
            status = "same program, same answer"
        row["Comparison"] = status
        rows.append(row)
    return pd.DataFrame(rows)


def build_federated_table(federated: list[dict]) -> pd.DataFrame:
    """One row per round: the program tested, what each client answered and
    the aggregated answer (used when there is no client 0 to compare with)."""
    n_clients = max(
        (len(e.get("client_outcomes") or []) for e in federated), default=0
    )
    rows = []
    for index, fed in enumerate(federated):
        row: dict = {"Round": index + 1, "Program": _program(fed["hypothesis"])}
        per_client = {c["client"]: c for c in (fed.get("client_outcomes") or [])}
        for client in range(1, n_clients + 1):
            c = per_client.get(client)
            row[f"Client {client}"] = (
                f"{_outcome(c['epsilon_positive'], c['epsilon_negative'])}  ({c['score']:g})"
                if c
                else "—"
            )
        row["Aggregated"] = _outcome(fed["epsilon_positive"], fed["epsilon_negative"])
        row["Score"] = fed["score"]
        rows.append(row)
    return pd.DataFrame(rows)


def _render_federated_only(benchmark_id: int) -> None:
    runs = _runs(benchmark_id)
    if not runs:
        st.info("No run in this benchmark yet.")
        return
    run = st.selectbox(
        "Run to inspect",
        options=sorted(runs),
        format_func=lambda r: f"Run {r}",
        key="hypothesis_run_fed_only",
    )
    federated = _load_log(runs[run])
    if not federated:
        st.info(
            "No hypothesis log for this run: it was launched before the tested programs "
            "were recorded. Relaunch the benchmark to see this table."
        )
        return
    table = build_federated_table(federated)
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.caption(
        "Programs tested by the federated search, in order. An answer is “positives covered / "
        "negatives covered”, each ALL, SOME or NONE; a program is a solution when it is "
        "ALL / NONE. Each “Client i” column is what client i answered on its own part of the "
        "examples (score in brackets); “Aggregated” is what the server builds from them. "
        "Launch the benchmark with “Hybrid evaluation” ticked to compare it, round by round, "
        "with Client 0 (centralized)."
    )
    st.download_button(
        "Download this table (CSV)",
        table.to_csv(index=False).encode("utf-8"),
        file_name=f"hypotheses_{benchmark_id}_run_{run}.csv",
        mime="text/csv",
        key="hypothesis_csv_fed_only",
    )


def render_hypothesis_tab(
    benchmark_id: int, federated_of: int | None, is_client_zero: bool
) -> None:
    federated_id = federated_of if is_client_zero else benchmark_id
    if federated_id is None:
        st.info("The federated benchmark linked to this one was not found.")
        return

    twin_id = _twin_benchmark(federated_id)
    if twin_id is None:
        st.info(
            "This benchmark has no “Client 0 (centralized)” search to compare with "
            "(it was launched without “Hybrid evaluation”). The programs of the federated "
            "search are shown below."
        )
        _render_federated_only(federated_id)
        return

    federated_runs, central_runs = _runs(federated_id), _runs(twin_id)
    common = sorted(set(federated_runs) & set(central_runs))
    if not common:
        st.info("No run exists in both searches yet.")
        return

    st.markdown(
        "Round-by-round comparison of the two complete searches of the hybrid evaluation: "
        f"the **federated** one (experiment benchmark #{federated_id}, clients 1..K) and "
        f"**Client 0 (centralized)** (benchmark #{twin_id}, one client holding the whole dataset)."
    )

    run = st.selectbox(
        "Run to inspect",
        options=common,
        format_func=lambda r: f"Run {r}",
        key="hypothesis_run",
    )
    federated = _load_log(federated_runs[run])
    central = _load_log(central_runs[run])

    if not federated or not central:
        st.info(
            "No hypothesis log for this run: it was launched before Coordination recorded "
            "the tested programs. Relaunch the benchmark to see this table."
        )
        return

    table = build_table(federated, central)

    first_diff = table.index[table["Comparison"] == "FIRST DIFFERENT PROGRAM"].tolist()
    answer_diff = int((table["Comparison"] == "same program, DIFFERENT answer").sum())
    identical_prefix = (first_diff[0] if first_diff else min(len(federated), len(central)))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Programs tested (federated)", len(federated))
    c2.metric("Programs tested (client 0)", len(central))
    c3.metric(
        "First different program",
        f"round {first_diff[0] + 1}" if first_diff else "none",
    )
    c4.metric("Same program, different answer", answer_diff)

    if first_diff:
        st.caption(
            f"The two searches test exactly the same {identical_prefix} programs, then part at "
            f"round {first_diff[0] + 1}. Look at the row just before it: if the answers agree there, "
            "the difference comes from the search itself; if they disagree, the aggregation "
            "of the clients differs from testing on the whole dataset."
        )
    else:
        st.caption("Both searches tested the same programs in the same order.")

    view = st.radio(
        "Rows to show",
        ["Around the first difference", "Only rows that differ", "All rounds"],
        horizontal=True,
        index=0 if first_diff else 2,
        key="hypothesis_view",
    )
    shown = table
    if view == "Only rows that differ":
        shown = table[~table["Comparison"].isin(["same program, same answer"])]
    elif view == "Around the first difference" and first_diff:
        lo, hi = max(first_diff[0] - 5, 0), first_diff[0] + 6
        shown = table.iloc[lo:hi]

    st.dataframe(
        shown,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Round": st.column_config.NumberColumn(width="small"),
            "Federated — score": st.column_config.NumberColumn(format="%.0f"),
            "Client 0 — score": st.column_config.NumberColumn(format="%.0f"),
        },
    )

    st.caption(
        "**How to read it.** An answer is “positives covered / negatives covered”, each ALL, SOME "
        "or NONE; a program is a solution when it is ALL / NONE. Each “Client i” column is what "
        "client i answered on its own part of the examples, with its score in brackets. "
        "“Federated — aggregated” is what the server builds from them (ALL only if every client says "
        "ALL, NONE only if every client says NONE, SOME otherwise; the score is the sum). "
        "“Client 0” is the answer of the single client holding all the examples."
    )

    st.download_button(
        "Download this table (CSV)",
        table.to_csv(index=False).encode("utf-8"),
        file_name=f"hypotheses_federated_{federated_id}_run_{run}.csv",
        mime="text/csv",
        key="hypothesis_csv",
    )
