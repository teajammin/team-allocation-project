from django.test import SimpleTestCase

from allocations.allocator.team_sizes import team_sizes


# Tests of team_sizes function
class TeamSizesTestCase(SimpleTestCase):

    def test_zero_students_gives_no_teams(self):
        self.assertEqual(team_sizes(0, 4, 5), [])

    def test_seven_students_is_impossible(self):
        self.assertIsNone(team_sizes(7, 4, 5))

    def test_invalid_size_limits_are_rejected(self):
        for min_size, max_size in [(0, 0), (0, 5), (5, 4)]:
            with self.subTest(min_size=min_size, max_size=max_size):
                with self.assertRaises(ValueError):
                    team_sizes(10, min_size, max_size)

    def test_twenty_two_students_gives_fewest_even_teams(self):
        self.assertEqual(team_sizes(22, 4, 5), [5, 5, 4, 4, 4])

    def test_sizes_are_valid_or_none_for_every_cohort(self):
        for num_students in range(51):
            with self.subTest(num_students=num_students):
                sizes = team_sizes(num_students, 4, 5)
                if sizes is not None:
                    self.assertEqual(sum(sizes), num_students)
                    self.assertTrue(all(4 <= size <= 5 for size in sizes))

    def test_boundary_cohorts_for_four_to_five(self):
        expected = {7: None, 8: [4, 4], 9: [5, 4], 10: [5, 5], 11: None}
        for num_students, sizes in expected.items():
            with self.subTest(num_students=num_students):
                self.assertEqual(team_sizes(num_students, 4, 5), sizes)

    def test_equal_limits_need_an_exact_multiple(self):
        self.assertEqual(team_sizes(9, 3, 3), [3, 3, 3])
        self.assertIsNone(team_sizes(10, 3, 3))

    def test_fewer_students_than_minimum_is_impossible(self):
        self.assertIsNone(team_sizes(3, 4, 5))
