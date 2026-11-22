from unittest import TestCase
from hypothesis import given, strategies as st
from allocations.allocator.team_sizes import team_sizes

COHORT_SIZES = st.integers(min_value=0, max_value=400)
SMALLEST_TEAMS = st.integers(min_value=1, max_value=8)
EXTRA_ROOM = st.integers(min_value=0, max_value=4)


class TeamSizesPropertyTests(TestCase):
    """Rules that team_sizes need to follow for any cohort and any size limits"""
    @given(COHORT_SIZES, SMALLEST_TEAMS, EXTRA_ROOM)
    def test_sizes_fit_cohort_or_impossible(self, cohort, smallest, extra):
        largest = smallest + extra
        sizes = team_sizes(cohort, smallest, largest)
        if sizes is None:
            return
        self.assertEqual(sum(sizes), cohort)
        self.assertTrue(all(smallest <= size <= largest for size in sizes))

    @given(COHORT_SIZES, SMALLEST_TEAMS, EXTRA_ROOM)
    def test_impossible(self, cohort, smallest, extra):
        largest = smallest + extra
        if team_sizes(cohort, smallest, largest) is not None:
            return
        workable = [
            teams
            for teams in range(1, cohort + 1)
            if teams * smallest <= cohort <= teams * largest
        ]
        self.assertEqual(workable, [])
