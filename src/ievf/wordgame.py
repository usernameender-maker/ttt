"""Small deterministic word-scoring and word-ladder helpers.

This module is a local game prototype. It does not download corpora or make
language-prediction claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import AbstractSet, Sequence


_LETTER_SCORES = {
    **dict.fromkeys("aeioul nstr".replace(" ", ""), 1),
    "d": 2, "g": 2,
    "b": 3, "c": 3, "m": 3, "p": 3,
    "f": 4, "h": 4, "v": 4, "w": 4, "y": 4,
    "k": 5,
    "j": 8, "x": 8,
    "q": 10, "z": 10,
}


@dataclass(frozen=True)
class WordMove:
    """A submitted word and its deterministic score at a one-based turn."""

    word: str
    score: int
    turn: int


def letter_score(ch: str) -> int:
    """Return the English-letter score; non-ASCII or non-letter characters score zero."""
    if not isinstance(ch, str) or len(ch) != 1:
        raise ValueError("letter_score expects exactly one character")
    return _LETTER_SCORES.get(ch.lower(), 0)


def score_word(word: str) -> int:
    """Sum per-character scores; punctuation and unsupported letters score zero."""
    if not isinstance(word, str):
        raise TypeError("word must be a string")
    return sum(letter_score(ch) for ch in word)


def build_word_game(words: Sequence[str]) -> list[WordMove]:
    """Convert words into ordered moves with deterministic scores."""
    if isinstance(words, (str, bytes)):
        raise TypeError("words must be a sequence of words, not a string")
    return [WordMove(word=word, score=score_word(word), turn=i) for i, word in enumerate(words, 1)]


def best_move(words: Sequence[str]) -> WordMove:
    """Return the highest-scoring move; ties select the earliest move."""
    moves = build_word_game(words)
    if not moves:
        raise ValueError("Cannot find best move from an empty word list.")
    return max(moves, key=lambda move: move.score)


def is_valid_word_chain(prev: str, nxt: str) -> bool:
    """Return whether two non-empty, equal-length words differ in one position.

    Comparison is case-insensitive. This helper checks the ladder rule only;
    it does not check dictionary membership.
    """
    if not isinstance(prev, str) or not isinstance(nxt, str):
        return False
    if not prev or len(prev) != len(nxt):
        return False
    return sum(a.casefold() != b.casefold() for a, b in zip(prev, nxt)) == 1


def validate_word_sequence(
    sequence: Sequence[str], dictionary: AbstractSet[str] | None = None
) -> bool:
    """Validate a word ladder and, if supplied, membership in a local dictionary.

    The dictionary is expected to contain normalized lowercase words. Passing an
    empty set therefore rejects every non-empty sequence.
    """
    if isinstance(sequence, (str, bytes)) or not sequence:
        return False
    if any(not isinstance(word, str) or not word for word in sequence):
        return False
    if dictionary is not None and any(word.casefold() not in dictionary for word in sequence):
        return False
    return all(is_valid_word_chain(a, b) for a, b in zip(sequence, sequence[1:]))


__all__ = [
    "WordMove", "best_move", "build_word_game", "is_valid_word_chain",
    "letter_score", "score_word", "validate_word_sequence",
]
