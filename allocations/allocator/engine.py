"""The entry point for generating team allocations."""

from allocations.allocator.initial_allocation import initial_allocation
from allocations.allocator.result import AllocationResult, Status
from allocations.allocator.team_sizes import team_sizes


def allocate(students, min_size, max_size):
    """Allocate students into teams of min_size to max_size students."""
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
    teams = initial_allocation(students, sizes)
    return AllocationResult(
        Status.SUCCESS, 
        teams, 
        f"{num_students},students allocated into {len(teams)} teams."
    )
