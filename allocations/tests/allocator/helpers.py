"""Shared helpers for allocator tests."""

from types import SimpleNamespace


def make_students(scores):
    """Return stand-in students with given c-scores."""
    return [SimpleNamespace(id=number, c_score=score) for number, score in enumerate(scores)]
