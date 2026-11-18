"""Build a first allocation by grouping students together with similar c-scores."""

from allocations.allocator.team import Team


def initial_allocation(students, sizes):
    """Return teams of the given sizes, filled in order of c-score.
    
    Students without c-score are placed after everyone else.
    Raises ValueError if the sizes do not add up to the number of students.
    """

    if sum(sizes) != len(students):
        raise ValueError("Team sizes must add up to the number of students.")
    ordered = _sort_by_c_score(students)
    teams = []
    start = 0
    for number, size in enumerate(sizes, start=1):
        teams.append(Team(f"Team {number}", ordered[start:start + size]))
        start += size
    return teams

def _sort_by_c_score(students):
    """Return students sorted by c-score, with missing scores last."""
    scored = [student for student in students if student.c_score is not None]
    unscored = [student for student in students if student.c_score is None]
    return sorted(scored, key=lambda student: student.c_score) + unscored
