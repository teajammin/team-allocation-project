from types import SimpleNamespace

from django.test import SimpleTestCase

from allocations.policies.team_size import TeamSizePolicy


def make_team(name, size):
    return SimpleNamespace(name=name, students=[object()] * size)


class TeamSizePolicyTests(SimpleTestCase):
    def setUp(self):
        self.policy = TeamSizePolicy(min_size=4, max_size=5)

    def test_teams_at_min_and_max_pass(self):
        teams = [make_team("Team 1", 4), make_team("Team 2", 5)]
        self.assertEqual(self.policy.evaluate(teams), [])

    def test_team_below_min_fails(self):
        violations = self.policy.evaluate([make_team("Team 1", 3)])
        self.assertEqual(len(violations), 1)

    def test_team_above_max_fails(self):
        violations = self.policy.evaluate([make_team("Team 1", 6)])
        self.assertEqual(len(violations), 1)

    def test_empty_team_fails(self):
        violations = self.policy.evaluate([make_team("Team 1", 0)])
        self.assertEqual(len(violations), 1)

    def test_message_names_team_and_size(self):
        violations = self.policy.evaluate([make_team("Team 3", 6)])
        self.assertEqual(violations[0].team_name, "Team 3")
        self.assertIn("6 students", violations[0].message)

    def test_hard_by_default(self):
        violations = self.policy.evaluate([make_team("Team 1", 6)])
        self.assertTrue(violations[0].is_hard)

    def test_soft_flag_is_carried_over(self):
        soft_policy = TeamSizePolicy(min_size=4, max_size=5, is_hard=False)
        violations = soft_policy.evaluate([make_team("Team 1", 6)])
        self.assertFalse(violations[0].is_hard)
