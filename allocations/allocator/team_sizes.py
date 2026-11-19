"""Work out how many students go in each team."""


def team_sizes(num_students, min_size, max_size):
    """Return a list of team sizes using the fewest teams possible.
    Each size is between min_size and max_size, and the sizes add up to num_students.
    Return [] for 0 students, or None if the students cannot be split within size limits."""

    if min_size < 1 or max_size < min_size:
        raise ValueError("Team sizes need 1 <= min_size <= max_size.")

    if num_students == 0:
        return []

    teams = 1
    while teams * min_size <= num_students:  # Keep going while this many teams could still fit
        if num_students <= teams * max_size:  # Can all students fit if every team is at its biggest
            base = num_students // teams
            extra = num_students % teams
            return [base + 1] * extra + [base] * (teams - extra)
        teams = teams + 1
    return None
