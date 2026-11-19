from types import SimpleNamespace

from django.test import SimpleTestCase

from allocations.policies.gender import MAN, OTHER, WOMAN, GenderPolicy


def make_team(name, *genders):
    students = [SimpleNamespace(gender=g) for g in genders]
    return SimpleNamespace(name=name, students=students)


class GenderPolicyTests(SimpleTestCase):
    def setUp(self):
        self.policy = GenderPolicy(priority=1)

    def check(self, *genders):
        return self.policy.evaluate([make_team("Team 1", *genders)])

    def test_two_women_two_men_passes(self):
        self.assertEqual(self.check(WOMAN, WOMAN, MAN, MAN), [])

    def test_single_gender_team_passes(self):
        self.assertEqual(self.check(MAN, MAN, MAN, MAN), [])

    def test_lone_woman_fails(self):
        violations = self.check(WOMAN, MAN, MAN, MAN)
        self.assertEqual(len(violations), 1)
        self.assertIn("only one woman", violations[0].message)

    def test_lone_man_fails(self):
        violations = self.check(MAN, WOMAN, WOMAN, WOMAN)
        self.assertEqual(len(violations), 1)
        self.assertIn("only one man", violations[0].message)

    def test_undisclosed_students_are_ignored(self):
        self.assertEqual(self.check(WOMAN, WOMAN, MAN, MAN, None), [])

    def test_all_undisclosed_passes(self):
        self.assertEqual(self.check(None, None, None, None), [])

    def test_lone_disclosed_woman_with_undisclosed_others_fails(self):
        violations = self.check(WOMAN, None, None, None)
        self.assertEqual(len(violations), 1)

    def test_lone_other_in_diverse_team_passes(self):
        self.assertEqual(self.check(OTHER, WOMAN, WOMAN, MAN, MAN), [])

    def test_lone_other_in_single_gender_team_fails(self):
        violations = self.check(OTHER, MAN, MAN, MAN, MAN)
        self.assertEqual(len(violations), 1)

    def test_two_others_pass(self):
        self.assertEqual(self.check(OTHER, OTHER, MAN, MAN), [])

    def test_soft_by_default(self):
        violations = self.check(WOMAN, MAN, MAN, MAN)
        self.assertFalse(violations[0].is_hard)