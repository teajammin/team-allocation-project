from django.test import TestCase

from allocations.allocator.team_sizes import team_sizes

# Tests of team_sizes function
class TeamSizesTestCase(TestCase):

    def test_zero_students_gives_no_teams(self):
        self.assertEqual(team_sizes(0, 4, 5), [])

    def test_seven_students_is_impossible(self):
        self.assertIsNone(team_sizes(7, 4, 5))