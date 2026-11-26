"""The entry point for generating team allocations."""

import random
import time

from allocations.policies.team_size import TeamSizePolicy
from allocations.allocator.initial_allocation import initial_allocation
from allocations.allocator.search import improve
from allocations.allocator.result import AllocationResult, Status
from allocations.allocator.team_sizes import team_sizes
from allocations.policies.base import get_violations


DEFAULT_TIME_LIMIT = 20.0


def allocate(students, policies, seed=None, time_limit=DEFAULT_TIME_LIMIT):
    """Allocate students into teams that follow the given policies."""
    size_policy = _team_size_policy(policies)
    min_size, max_size = size_policy.min_size, size_policy.max_size
    num_students = len(students)

    if num_students == 0:
        return AllocationResult(Status.SUCCESS, [], "There are no eligible students to allocate.")

    sizes = team_sizes(num_students, min_size, max_size)

    if sizes is None:
        return AllocationResult(
            Status.INFEASIBLE,
            None,
            f"{num_students} students cannot be split into teams of "
            f"{min_size}-{max_size}. Change the team size limits."
        )

    deadline = time.monotonic() + time_limit
    teams = initial_allocation(students, sizes)
    improve(teams, policies, random.Random(seed), deadline)
    return _final_result(teams, policies, num_students, time_limit)


def _final_result(teams, policies, num_students, time_limit):
    """Return SUCCESS with any unmet soft conditions, or TIME_OUT if a hard condition is still broken."""
    violations = get_violations(teams, policies)
    hard_violations = [violation for violation in violations if violation.is_hard]
    if hard_violations:
        return AllocationResult(
            Status.TIMED_OUT,
            None,
            f"No allocation meeting every hard condition was found within {time_limit:g} seconds. "
            "This does not mean that no such allocation exists.",
            hard_violations,
        )
    return AllocationResult(
        Status.SUCCESS,
        teams,
        f"{num_students} students allocated into {len(teams)} teams.",
        violations,
    )


def _team_size_policy(policies):
    """Return the TeamSizePolicy from policies."""
    for policy in policies:
        if isinstance(policy, TeamSizePolicy):
            return policy
    raise ValueError("An allocation policy must include a team size.")
