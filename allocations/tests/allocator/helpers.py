"""Shared helpers for allocator tests."""

from types import SimpleNamespace


def make_students(scores):
    """Return stand-in students with given c-scores."""
    return [SimpleNamespace(id=number, c_score=score) for number, score in enumerate(scores)]


def make_student(number, c_score=None, gender=None, ethnicity=None, extra=None):
    """Return a stand-in student with the given attributes."""
    return SimpleNamespace(id=number, c_score=c_score, gender=gender, ethnicity=ethnicity, extra=extra)
