from django.test import SimpleTestCase

from allocations.allocator.initial_allocation import initial_allocation
from allocations.allocator.team_sizes import team_sizes
from allocations.tests.allocator.helpers import make_students


# Tests of initial allocation
class InitialAllocationTestCase(SimpleTestCase):

    def test_every_student_appears_exactly_once_in_teams_of_the_right_size(self):
        for num_students in range(51):
            sizes = team_sizes(num_students, 4, 5)
            if sizes is None:
                continue
            with self.subTest(num_students=num_students):
                students = make_students(range(num_students))
                teams = initial_allocation(students, sizes)
                allocated = [student for team in teams for student in team.students]
                self.assertCountEqual(allocated, students)
                self.assertEqual([len(team.students) for team in teams], sizes)

    def test_teams_are_filled_from_lowest_to_highest_c_score(self):
        students = make_students([70, 50, 90, 60, 80, 40, 55, 65, 75])
        teams = initial_allocation(students, [5, 4])
        first_scores = [student.c_score for student in teams[0].students]
        second_scores = [student.c_score for student in teams[1].students]
        self.assertLessEqual(max(first_scores), min(second_scores))

    def test_students_without_a_c_score_are_placed_last(self):
        students = make_students([None, 60, 40, None, 50, 70, 80, 90])
        teams = initial_allocation(students, [4, 4])
        last_scores = [student.c_score for student in teams[1].students]
        self.assertEqual(last_scores[-2:], [None, None])

    def test_sizes_that_do_not_match_the_cohort_are_rejected(self):
        with self.assertRaises(ValueError):
            initial_allocation(make_students([50, 60, 70]), [4])
