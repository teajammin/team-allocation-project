from django.test import SimpleTestCase

from allocations.allocator.engine import allocate
from allocations.allocator.result import Status
from allocations.policies.team_size import TeamSizePolicy
from allocations.tests.allocator.helpers import make_students
from allocations.policies.base import get_violations

FOUR_TO_FIVE = [TeamSizePolicy(min_size=4, max_size=5)]


# Tests of allocate
class AllocateTestCase(SimpleTestCase):

    def test_impossible_team_sizes_are_infeasible(self):
        result = allocate(make_students(range(7)), FOUR_TO_FIVE)
        self.assertEqual(result.status, Status.INFEASIBLE)
        self.assertIsNone(result.teams)
        self.assertIn("7 students", result.message)

    def test_feasible_cohort_allocates_every_student_once(self):
        students = make_students(range(22))
        result = allocate(students, FOUR_TO_FIVE)
        self.assertEqual(result.status, Status.SUCCESS)
        allocated = [student for team in result.teams for student in team.students]
        self.assertCountEqual(allocated, students)
        for team in result.teams:
            self.assertTrue(4 <= len(team.students) <= 5)
        self.assertEqual(len(result.teams), 5)

    def test_empty_cohort_succeeds_with_no_teams(self):
        result = allocate([], FOUR_TO_FIVE)
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertEqual(result.teams, [])

    def test_success_message_counts_students_and_teams(self):
        result = allocate(make_students(range(22)), FOUR_TO_FIVE)
        self.assertEqual(result.message, "22 students allocated into 5 teams.")

    def test_policies_without_team_size_are_rejected(self):
        with self.assertRaises(ValueError):
            allocate(make_students(range(8)), [])

    def test_successful_teams_have_no_team_size_violations(self):
        result = allocate(make_students(range(22)), FOUR_TO_FIVE)
        self.assertEqual(get_violations(result.teams, FOUR_TO_FIVE), [])
