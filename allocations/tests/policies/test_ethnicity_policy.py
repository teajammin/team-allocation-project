from types import SimpleNamespace

from django.test import SimpleTestCase

from allocations.policies.ethnicity import UNKNOWN, EthnicityPolicy


def make_team(name, *ethnicities):
    students = [SimpleNamespace(ethnicity=e) for e in ethnicities]
    return SimpleNamespace(name=name, students=students)


class EthnicityPolicyTests(SimpleTestCase):
    def setUp(self):
        self.policy = EthnicityPolicy(priority=3)

    def check(self, *ethnicities):
        return self.policy.evaluate([make_team("Team 1", *ethnicities)])

    def test_pairs_pass(self):
        self.assertEqual(self.check("1", "1", "4", "4"), [])

    def test_single_ethnicity_team_passes(self):
        self.assertEqual(self.check("4", "4", "4", "4"), [])

    def test_lone_member_fails(self):
        violations = self.check("2", "4", "4", "4")
        self.assertEqual(len(violations), 1)
        self.assertIn("only one Black", violations[0].message)

    def test_two_lone_members_give_two_violations(self):
        violations = self.check("1", "2", "4", "4")
        self.assertEqual(len(violations), 2)

    def test_none_is_ignored(self):
        self.assertEqual(self.check("1", "1", None, None), [])

    def test_unknown_code_is_ignored(self):
        self.assertEqual(self.check(UNKNOWN, "4", "4", "4"), [])

    def test_all_undisclosed_passes(self):
        self.assertEqual(self.check(None, None, None, None), [])

    def test_unavoidable_when_only_one_in_cohort(self):
        violations = self.check("2", "4", "4", "4")
        self.assertTrue(violations[0].is_unavoidable)
        self.assertIn("unavoidable", violations[0].message)

    def test_avoidable_when_others_exist_elsewhere(self):
        teams = [
            make_team("Team 1", "2", "4", "4", "4"),
            make_team("Team 2", "2", "4", "4", "4"),
        ]
        violations = self.policy.evaluate(teams)
        self.assertEqual(len(violations), 2)
        self.assertFalse(violations[0].is_unavoidable)
