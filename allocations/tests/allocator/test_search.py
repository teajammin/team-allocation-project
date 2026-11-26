import random
import time

from django.test import SimpleTestCase

from allocations.allocator.initial_allocation import initial_allocation
from allocations.allocator.search import improve
from allocations.policies.attainment import AttainmentPolicy
from allocations.policies.base import allocation_penalty, get_violations
from allocations.policies.ethnicity import EthnicityPolicy
from allocations.policies.gender import MAN, WOMAN, GenderPolicy
from allocations.policies.team_size import TeamSizePolicy
from allocations.tests.allocator.helpers import make_student

GENDER = [TeamSizePolicy(min_size=4, max_size=5), GenderPolicy(priority=1)]
MIXED = GENDER + [EthnicityPolicy(priority=2)]


def mixed_cohort(size):
    """Return a cohort with varied genders, ethnicities and c-scores."""
    rng = random.Random(size)
    return [
        make_student(number, c_score=rng.randint(30, 90),
                     gender=rng.choice([WOMAN, MAN, None]), ethnicity=rng.choice(["1", "2", "3", "4", None]))
        for number in range(size)
    ]


def ids_by_team(teams):
    """Return each team's student ids, so two allocations can be compared."""
    return [[student.id for student in team.students] for team in teams]


def run_improve(teams, policies, seed=1, seconds=5, max_swaps=500):
    """Run improve with a short deadline and a swap limit, so tests are repeatable."""
    improve(teams, policies, random.Random(seed), time.monotonic() + seconds, max_swaps)


class ImproveTestCase(SimpleTestCase):

    def test_penalty_never_gets_worse(self):
        teams = initial_allocation(mixed_cohort(22), [5, 5, 4, 4, 4])
        before = allocation_penalty(teams, MIXED)
        run_improve(teams, MIXED)
        self.assertLessEqual(allocation_penalty(teams, MIXED), before)

    def test_every_student_stays_exactly_once_in_teams_of_the_same_size(self):
        students = mixed_cohort(22)
        teams = initial_allocation(students, [5, 5, 4, 4, 4])
        run_improve(teams, MIXED)
        allocated = [student for team in teams for student in team.students]
        self.assertCountEqual(allocated, students)
        self.assertEqual([len(team.students) for team in teams], [5, 5, 4, 4, 4])

    def test_same_seed_gives_the_same_teams(self):
        first = initial_allocation(mixed_cohort(22), [5, 5, 4, 4, 4])
        second = initial_allocation(mixed_cohort(22), [5, 5, 4, 4, 4])
        run_improve(first, MIXED, seed=7)
        run_improve(second, MIXED, seed=7)
        self.assertEqual(ids_by_team(first), ids_by_team(second))

    def test_lone_women_are_moved_into_mixed_teams(self):
        genders = [WOMAN, MAN, MAN, MAN, WOMAN, WOMAN, WOMAN, MAN]
        students = [make_student(n, c_score=n, gender=g) for n, g in enumerate(genders)]
        teams = initial_allocation(students, [4, 4])
        self.assertNotEqual(get_violations(teams, GENDER), [])
        run_improve(teams, GENDER)
        self.assertEqual(get_violations(teams, GENDER), [])

    def test_swaps_that_make_things_worse_are_undone(self):
        policies = [TeamSizePolicy(min_size=4, max_size=4), GenderPolicy(priority=1),
                    AttainmentPolicy(max_spread=10, priority=2)]
        scores = [0, 0, 0, 0, 100, 100, 100, 100]
        genders = [WOMAN, MAN, MAN, MAN, MAN, MAN, MAN, MAN]
        students = [make_student(n, c_score=c, gender=g) for n, (c, g) in enumerate(zip(scores, genders))]
        teams = initial_allocation(students, [4, 4])
        before = ids_by_team(teams)
        run_improve(teams, policies)
        self.assertEqual(ids_by_team(teams), before)

    def test_a_single_team_is_left_alone(self):
        teams = initial_allocation(mixed_cohort(5), [5])
        before = ids_by_team(teams)
        run_improve(teams, MIXED)
        self.assertEqual(ids_by_team(teams), before)

    def test_nothing_changes_once_the_deadline_has_passed(self):
        teams = initial_allocation(mixed_cohort(22), [5, 5, 4, 4, 4])
        before = ids_by_team(teams)
        improve(teams, MIXED, random.Random(1), time.monotonic() - 1)
        self.assertEqual(ids_by_team(teams), before)

    def test_a_perfect_allocation_is_not_changed(self):
        students = [make_student(number, c_score=number, gender=MAN) for number in range(8)]
        teams = initial_allocation(students, [4, 4])
        before = ids_by_team(teams)
        improve(teams, GENDER, random.Random(1), time.monotonic() + 5)
        self.assertEqual(ids_by_team(teams), before)
