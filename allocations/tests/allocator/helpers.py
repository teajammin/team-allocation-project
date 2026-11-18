"""Shared helpers for allocator tests."""

from types import SimpleNamespace


def make_students(scores):
    """Return stand-in students with given c-scores."""
    return [SimpleNamespace(c_score=score) for score in scores]
