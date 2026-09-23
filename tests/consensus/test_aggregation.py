from engines.consensus.aggregation import (
    majority_threshold,
    majority_vote,
)


def test_majority_threshold():
    assert majority_threshold(1) == 1
    assert majority_threshold(2) == 2
    assert majority_threshold(3) == 2
    assert majority_threshold(10) == 6


def test_two_hypotheses_strict_majority():
    h1 = {
        "a": True,
        "b": True,
        "c": False,
        "d": False,
    }

    h2 = {
        "a": True,
        "b": False,
        "c": True,
        "d": False,
    }

    result = majority_vote([h1, h2])

    assert result == {
        "a": True,    # 2/2
        "b": False,   # 1/2 -> NEG
        "c": False,   # 1/2 -> NEG
        "d": False,   # 0/2
    }


def test_empty_hypothesis_is_still_a_voter():
    learned_hypothesis = {
        "a": True,
        "b": False,
    }

    empty_hypothesis = {
        "a": False,
        "b": False,
    }

    result = majority_vote(
        [
            learned_hypothesis,
            empty_hypothesis,
        ]
    )

    assert result == {
        "a": False,   # 1/2 -> NEG
        "b": False,
    }


def test_three_hypotheses():
    h1 = {"a": True, "b": False}
    h2 = {"a": True, "b": True}
    h3 = {"a": False, "b": True}

    result = majority_vote([h1, h2, h3])

    assert result == {
        "a": True,   # 2/3
        "b": True,   # 2/3
    }