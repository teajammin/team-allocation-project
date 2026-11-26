from django.test import SimpleTestCase
from hypothesis import given, strategies as st

from allocations.allocator.engine import allocate
from allocations.allocator.result import Status
from allocations.allocator.team_sizes import team_sizes
from allocations.policies.base import get_violations
from allocations.policies.team_size import TeamSizePolicy
from allocations.tests.allocator.helpers import make_students

MOST_STUDENTS = 120
BIGGEST_MIN_SIZE = 8
BIGGEST_SPARE = 4

COHORT_MARKS = st.lists(
    st.one_of(st.none(), st.integers(0, 100)), max_size=MOST_STUDENTS
)
SMALLEST_SIZE = st.integers(min_value=1, max_value=BIGGEST_MIN_SIZE)
SPARE_PLACES = st.integers(min_value=0, max_value=BIGGEST_SPARE)


def allocate_cohort(marks, smallest, spare):
    """make students from the marks and allocate them"""
    students = make_students(marks)
    policy = TeamSizePolicy(min_size=smallest, max_size=smallest + spare)
    result = allocate(students, [policy])
    return students, policy, result


class AllocateGeneratedTests(SimpleTestCase):
    """run allocate() on generated cohorts and check the rules it hodls"""

    @given(COHORT_MARKS, SMALLEST_SIZE, SPARE_PLACES)
    def test_infeasible(self, marks, smallest, spare):
        students, _, result = allocate_cohort(marks, smallest, spare)
        sizes = team_sizes(len(students), smallest, smallest + spare)
        if sizes is None:
            self.assertEqual(result.status, Status.INFEASIBLE)
        else:
            self.assertEqual(result.status, Status.SUCCESS)

    @given(COHORT_MARKS, SMALLEST_SIZE, SPARE_PLACES)
    def test_nobody_lost_doubled(self, marks, smallest, spare):
        students, _, result = allocate_cohort(marks, smallest, spare)
        if result.status != Status.SUCCESS:
            return
        placed = []
        for team in result.teams:
            for student in team.students:
                placed.append(student)
        self.assertCountEqual(placed, students)

    @given(COHORT_MARKS, SMALLEST_SIZE, SPARE_PLACES)
    def test_no_team_violations(self, marks, smallest, spare):
        _, policy, result = allocate_cohort(marks, smallest, spare)
        if result.status != Status.SUCCESS:
            return
        self.assertEqual(get_violations(result.teams, [policy]), [])

    @given(COHORT_MARKS, SMALLEST_SIZE, SPARE_PLACES)
    def test_lowest_marks_first(self, marks, smallest, spare):
        _, _, result = allocate_cohort(marks, smallest, spare)
        if result.status != Status.SUCCESS:
            return
        marks_in_order = []
        for team in result.teams:
            for student in team.students:
                marks_in_order.append(student.c_score)
        real_marks = [mark for mark in marks_in_order if mark is not None]
        number_blank = len(marks_in_order) - len(real_marks)
        expected = sorted(real_marks) + [None] * number_blank
        self.assertEqual(marks_in_order, expected)
