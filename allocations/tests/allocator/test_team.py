from django.test import TestCase

from allocations.allocator.team import Team

class TeamTestCase(TestCase):

    def test_team_remembers_its_name(self):
        team = Team("Team 1", [])
        self.assertEqual(team.name, "Team 1")

    def test_team_remembers_its_students(self):
        students = ["ara", "amy"]
        team = Team("Team 1", students)
        self.assertEqual(team.students, students)