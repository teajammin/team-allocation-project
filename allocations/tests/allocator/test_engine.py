from django.test import SimpleTestCase

from allocations.allocator.engine import allocate
from allocations.allocator.result import Status
from allocations.tests.allocator.helpers import make_students


# Tests of allocate
class AllocateTestCase(SimpleTestCase):

    def test_impossible_team_sizes_are_infeasible(self):
        result = allocate(make_students(range(7)), 4, 5)
        self.assertEqual(result.status, Status.INFEASIBLE)
        self.assertIsNone(result.teams)
        self.assertIn("7 students", result.message)

    def test_feasible_cohort_allocates_every_student_once(self):
        students = make_students(range(22))
        result = allocate(students, 4, 5)
        self.assertEqual(result.status, Status.SUCCESS)
        allocated = [student for team in result.teams for student in team.students]
        self.assertCountEqual(allocated, students)
        for team in result.teams:
            self.assertTrue(4 <= len(team.students) <= 5)
        self.assertEqual(len(result.teams), 5)

    def test_empty_cohort_succeeds_with_no_teams(self):
        result = allocate([], 4, 5)
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertEqual(result.teams, [])
