from django.test import SimpleTestCase

from allocations.allocator.engine import allocate
from allocations.allocator.result import Status
from allocations.policies.team_size import TeamSizePolicy
from allocations.tests.allocator.helpers import make_students, make_student
from allocations.policies.base import get_violations
from allocations.policies.gender import MAN, WOMAN, GenderPolicy

FOUR_TO_FIVE = [TeamSizePolicy(min_size=4, max_size=5)]
HARD_GENDER = GenderPolicy(is_hard=True)


def alternating_genders():
    """Return 4 women and 4 men whose first allocation leaves a lone woman and a lone man."""
    genders = [WOMAN, MAN, MAN, MAN, WOMAN, WOMAN, WOMAN, MAN]
    return [make_student(number, c_score=number, gender=gender) for number, gender in enumerate(genders)]


def student_ids(teams):
    """Return each team's student ids, so two allocations can be compared."""
    return [[student.id for student in team.students] for team in teams]


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


# Tests of allocate with policies other than team size
class AllocateWithPoliciesTestCase(SimpleTestCase):

    def test_unmet_soft_conditions_are_reported_on_success(self):
        students = [make_student(n, c_score=n, gender=MAN) for n in range(7)] + [make_student(7, gender=WOMAN)]
        result = allocate(students, FOUR_TO_FIVE + [GenderPolicy()], time_limit=1)
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertEqual([v.policy_name for v in result.violations], ["Gender representation"])

    def test_search_fixes_a_broken_hard_condition(self):
        result = allocate(alternating_genders(), FOUR_TO_FIVE + [HARD_GENDER], time_limit=5)
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertEqual(result.violations, ())

    def test_hard_condition_still_broken_at_the_time_limit_is_timed_out(self):
        result = allocate(alternating_genders(), FOUR_TO_FIVE + [HARD_GENDER], time_limit=0)
        self.assertEqual(result.status, Status.TIMED_OUT)
        self.assertIsNone(result.teams)
        self.assertTrue(all(violation.is_hard for violation in result.violations))
        self.assertIn("does not mean that no such allocation exists", result.message)

    def test_same_seed_gives_the_same_teams(self):
        first = allocate(alternating_genders(), FOUR_TO_FIVE + [HARD_GENDER], seed=3, time_limit=5)
        second = allocate(alternating_genders(), FOUR_TO_FIVE + [HARD_GENDER], seed=3, time_limit=5)
        self.assertEqual(student_ids(first.teams), student_ids(second.teams))
