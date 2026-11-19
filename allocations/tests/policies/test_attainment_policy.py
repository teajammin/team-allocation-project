from types import SimpleNamespace

from django.test import SimpleTestCase

from allocations.policies.attainment import AttainmentPolicy


def make_team(name, *scores):
    students = [SimpleNamespace(c_score=s) for s in scores]
    return SimpleNamespace(name=name, students=students)


class AttainmentPolicyTests(SimpleTestCase):
    def setUp(self):
        self.policy = AttainmentPolicy(max_spread=15, priority=2)

    def check(self, *scores):
        return self.policy.evaluate([make_team("Team 1", *scores)])

    def test_spread_under_limit_passes(self):
        self.assertEqual(self.check(60.0, 65.0, 70.0), [])

    def test_spread_exactly_at_limit_passes(self):
        self.assertEqual(self.check(50.0, 65.0), [])

    def test_spread_just_over_limit_fails(self):
        violations = self.check(50.0, 66.0)
        self.assertEqual(len(violations), 1)

    def test_identical_marks_pass(self):
        self.assertEqual(self.check(70.0, 70.0, 70.0, 70.0), [])

    def test_missing_scores_are_skipped(self):
        self.assertEqual(self.check(60.0, None, 70.0, None), [])

    def test_all_missing_passes(self):
        self.assertEqual(self.check(None, None, None), [])

    def test_single_score_passes(self):
        self.assertEqual(self.check(80.0, None, None), [])

    def test_message_shows_spread_and_target(self):
        violations = self.check(40.0, 62.0)
        self.assertIn("mark spread of 22", violations[0].message)
        self.assertIn("target 15 or less", violations[0].message)

    def test_severity_is_amount_over_limit(self):
        violations = self.check(40.0, 62.0)
        self.assertEqual(violations[0].severity, 7)

    def test_soft_by_default(self):
        violations = self.check(40.0, 62.0)
        self.assertFalse(violations[0].is_hard)
