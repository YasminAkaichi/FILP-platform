"""LLM-assisted parsing of free-text background knowledge into Prolog
rules, for the Custom ILP tab.

Uses Google Gemini (free tier available via aistudio.google.com — no
credit card required), through the `google-generativeai` package.

Safety contract
----------------
This module NEVER trusts the LLM's output directly. Gemini is asked to
return strict JSON mapping each rule to a conclusion predicate and a
list of condition predicates; every single one of those strings is then
checked against the caller-supplied `known_predicates` list before any
Prolog text is generated. Anything that doesn't match exactly is
dropped and surfaced to the user as a warning, exactly like the
keyword-based parser in `core.tabular_to_ilp.parse_background_text`
does — a hallucinated or slightly-off predicate name can never reach
`bk.pl`. If the API call fails for any reason (no key, network error,
malformed response), this raises `LLMParsingUnavailable` so the caller
can fall back to the keyword parser instead of crashing the app.
"""

from __future__ import annotations

import json

DEFAULT_MODEL = "gemini-3.8-flash"


class LLMParsingUnavailable(Exception):
    """Raised whenever the LLM path can't be used — caller should fall
    back to the keyword-based parser (core.tabular_to_ilp.parse_background_text)."""


_SYSTEM_PROMPT = """You convert short domain-knowledge statements into structured rules for an inductive logic programming system.

You will be given:
1. A list of KNOWN PREDICATES (exact names, case-sensitive — use them verbatim, never invent new ones).
2. Free-text rules, one per line, in English or French (e.g. "if fever and cough then flu" / "si fievre et toux alors grippe").

For each line that expresses an "if ... then ..." / "si ... alors ..." style implication, output one object:
  {"conclusion": "<one known predicate, or null>", "conditions": ["<known predicate>", ...]}

Rules:
- Only use predicate names from the KNOWN PREDICATES list, copied EXACTLY as given (same case, same underscores).
- If a concept in the text does not clearly correspond to any known predicate, use null for that slot instead of guessing or inventing a name.
- If a line isn't an if/then-style rule, skip it entirely.
- Output ONLY a JSON array, no prose, no markdown code fences.
"""


def _get_client(api_key: str):
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise LLMParsingUnavailable(f"google-generativeai package not installed: {exc}") from exc
    genai.configure(api_key=api_key)
    return genai


def parse_background_text_with_llm(
    text: str,
    known_predicates: list[str],
    api_key: str,
    model: str = DEFAULT_MODEL,
) -> tuple[list[str], list[str]]:
    """Same contract as core.tabular_to_ilp.parse_background_text:
    returns (rules, warnings) — `rules` are ready-to-append Prolog
    clause strings, `warnings` explain anything that was skipped or
    couldn't be matched to a known predicate.

    Raises LLMParsingUnavailable if the API can't be reached, the key
    is missing/invalid, or the response can't be parsed — callers
    should catch this and fall back to the keyword parser rather than
    surfacing a raw exception to the user.
    """
    text = text.strip()
    if not text:
        return [], []
    if not api_key:
        raise LLMParsingUnavailable("No API key configured")

    genai = _get_client(api_key)

    try:
        gen_model = genai.GenerativeModel(model, system_instruction=_SYSTEM_PROMPT)
        response = gen_model.generate_content(
            f"KNOWN PREDICATES: {json.dumps(known_predicates)}\n\nTEXT:\n{text}",
            generation_config={"response_mime_type": "application/json"},
        )
        raw_text = response.text
    except Exception as exc:  # noqa: BLE001 — any API/network failure triggers fallback
        raise LLMParsingUnavailable(f"Gemini API call failed: {exc}") from exc

    raw_text = (raw_text or "").strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise LLMParsingUnavailable(f"Model didn't return valid JSON: {exc}") from exc

    if not isinstance(parsed, list):
        raise LLMParsingUnavailable("Model response was not a JSON array")

    known_set = set(known_predicates)
    rules: list[str] = []
    warnings: list[str] = []

    for item in parsed:
        if not isinstance(item, dict):
            warnings.append(f"Skipped malformed entry from the model: {item!r}")
            continue

        conclusion = item.get("conclusion")
        conditions = item.get("conditions")
        if not isinstance(conditions, list):
            conditions = []

        # --- Validation step: never trust the model's output directly.
        # Every predicate name it produced is checked against the
        # caller's own known_predicates list, verbatim, before it's
        # allowed anywhere near a generated Prolog clause. Anything
        # unmatched (including a hallucinated or slightly-renamed
        # predicate) is dropped here and reported as a warning instead.
        if conclusion not in known_set:
            warnings.append(f"Unrecognized conclusion predicate: {conclusion!r}")
            continue
        bad_conditions = [c for c in conditions if c not in known_set]
        if not conditions or bad_conditions:
            warnings.append(
                f"Rule for {conclusion!r} skipped — unrecognized condition(s): {bad_conditions or '(none given)'}"
            )
            continue

        body = ", ".join(f"{c}(S)" for c in conditions)
        rules.append(f"{conclusion}(S) :- {body}.")

    return rules, warnings


def chat_reply(history: list[dict], context: str, api_key: str, model: str = DEFAULT_MODEL) -> str:
    """One-shot chat call for the "Ask the AI about this data" box.

    `history` is a list of {"role": "user"|"model", "content": str}
    (already in the caller's chat order, last entry is the new user
    message). `context` is prepended as a system instruction so the
    model can answer questions about the specific dataset/run.
    """
    genai = _get_client(api_key)
    gen_model = genai.GenerativeModel(
        model,
        system_instruction=(
            "You are helping a user understand a dataset they just converted into an "
            "inductive logic programming (ILP) problem on the FILP platform. Answer "
            "concisely, in the same language the user writes in. Context:\n" + context
        ),
    )
    gemini_history = [
        {"role": ("model" if m["role"] == "assistant" else "user"), "parts": [m["content"]]}
        for m in history[:-1]
    ]
    chat = gen_model.start_chat(history=gemini_history)
    response = chat.send_message(history[-1]["content"])
    return response.text
