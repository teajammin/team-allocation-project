"""Improve an allocation by swapping students between teams."""

import time

from allocations.policies.base import allocation_penalty


def improve(teams, policies, rng, deadline, max_swaps=None):
    """Swap students between teams until the deadline, max_swaps or perfect score.

    Swaps never change team sizes. Change teams in place.
    """

    if len(teams) < 2:
        return
    swaps = 0
    scores = [allocation_penalty([team], policies) for team in teams]
    while _should_continue(scores, deadline, swaps, max_swaps):
        swaps += 1
        i, j = rng.sample(range(len(teams)), 2)
        first, second = teams[i].students, teams[j].students
        a, b = rng.randrange(len(first)), rng.randrange(len(second))
        first[a], second[b] = second[b], first[a]
        new_i = allocation_penalty([teams[i]], policies)
        new_j = allocation_penalty([teams[j]], policies)
        if _add(new_i, new_j) <= _add(scores[i], scores[j]):
            scores[i], scores[j] = new_i, new_j
        else:
            first[a], second[b] = second[b], first[a]


def _should_continue(scores, deadline, swaps, max_swaps):
    """Return True while there is time, swaps are left and some penalty remains."""
    if time.monotonic() >= deadline:
        return False
    if max_swaps is not None and swaps >= max_swaps:
        return False
    return any(any(score) for score in scores)


def _add(first, second):
    """Add two penalty tuples position by position."""
    return tuple(x + y for x, y in zip(first, second))
