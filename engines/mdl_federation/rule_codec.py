"""
Text <-> clause conversion for FedMDL (the federated version of MaxSynth /
noisy-MDL, symbolic/Popper-v3).

Popper 1.1.0 (popper-core) ships `Literal.from_string` / `Clause.from_string`
on its own `core.py`, which is what lets FedPopper (engines/collaboration)
round-trip a candidate rule through plain text between the server and its
clients. Popper-v3's own `popper_mdl/core.py` is a much slimmer rewrite — it
dropped those parsing helpers (and `__hash__`/`__eq__`) entirely, since the
centralized engine never needed to re-parse a rule it had just built from a
clingo model.

FedMDL needs that round-trip (server generates a candidate from its own ASP
model, sends it as text to every client, each client must turn that text
back into a `popper_mdl.core.Literal`-based rule its own local `Tester` can
query), so this module adds it back as a small, self-contained, pure-Python
parser — deliberately NOT patched into the vendored popper_mdl package
itself, to avoid touching third-party source we didn't write.

The wire format is exactly what `popper_mdl.util.format_rule` already
produces: `head(A,B):- body1(A,C),body2(C,B).` — one rule, a single `:-`,
comma-separated flat literals with no nested terms (matches
`parse_model_single_rule`'s single-rule, non-recursive, non-PI output,
which is the only program shape FedMDL's MVP generates/sends).

This parsing logic needs no Prolog/SWI-Prolog at all — it's plain string
manipulation — so it can be (and is, see tests/test_rule_codec.py) unit
tested without the `pyswip` dependency that the rest of this federated
engine needs at runtime.
"""

from __future__ import annotations

import re

from popper_mdl.core import Literal

_LITERAL_PATTERN = re.compile(r"\w+\([^()]*\)")


def _parse_literal(literal_text: str, directions: dict) -> Literal:
    """
    Parse a single flat literal like `piece(A,C)` into a popper_mdl Literal,
    using `settings.directions` (predicate -> {arg_index: '+'/'-'}) to
    restore the input/output argument modes a Literal needs for
    `popper_mdl.util.order_rule` to work correctly during testing — those
    modes aren't encoded in the text itself, only in the bias file, which
    both the server and every client parsed independently from the same
    bias.pl, so this lookup is always available locally.
    """
    predicate, args_part = literal_text.split("(", 1)
    predicate = predicate.strip()
    args_part = args_part.rstrip(")")

    arguments = (
        tuple(arg.strip() for arg in args_part.split(","))
        if args_part.strip()
        else tuple()
    )

    predicate_directions = directions.get(predicate) if directions else None
    if predicate_directions:
        modes = tuple(
            predicate_directions[index] for index in range(len(arguments))
        )
    else:
        modes = tuple("?" for _ in arguments)

    return Literal(predicate, arguments, modes)


def parse_rule(rule_text: str, directions: dict) -> tuple:
    """
    Parse `head(...):- body1(...),body2(...).` (as produced by
    popper_mdl.util.format_rule) into a (head, body) rule tuple — a
    popper_mdl Literal for the head, and a frozenset of popper_mdl Literals
    for the body — ready to wrap as `frozenset([rule])` and hand to
    popper_mdl.tester.Tester.test_single_rule_pos / ..._neg.

    `directions` is `settings.directions` from a popper_mdl.util.Settings
    object built from the SAME bias.pl the rule's predicates were declared
    in (client and server each build their own Settings from their own copy
    of that file, so this is always available without any extra network
    round-trip).
    """
    if ":-" not in rule_text:
        raise ValueError(f"Not a valid rule (missing ':-'): {rule_text!r}")

    head_text, body_text = rule_text.split(":-", 1)
    head_text = head_text.strip()
    body_text = body_text.strip()

    if body_text.endswith("."):
        body_text = body_text[:-1]

    head = _parse_literal(head_text, directions)

    body_literal_texts = _LITERAL_PATTERN.findall(body_text)
    body = frozenset(
        _parse_literal(literal_text, directions)
        for literal_text in body_literal_texts
    )

    return head, body


def rule_to_text(rule: tuple) -> str:
    """
    Serialize a (head, body) rule tuple to the same text format `parse_rule`
    reads back — a thin, explicitly-named wrapper around
    popper_mdl.util.format_rule so call sites in this package don't need to
    import from the vendored package directly just for this one function.
    """
    from popper_mdl.util import format_rule

    return format_rule(rule)
