from types import SimpleNamespace

from django.test import SimpleTestCase

from allocations.policies.gender import (
    MAN,
    NON_BINARY,
    UNKNOWN,
    WOMAN,
    GenderPolicy,
)


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

    def test_non_binary_student_is_ignored(self):
        self.assertEqual(self.check(NON_BINARY, MAN, MAN, MAN), [])

    def test_lone_non_binary_does_not_fail(self):
        self.assertEqual(self.check(NON_BINARY, WOMAN, WOMAN, MAN, MAN), [])

    def test_unknown_code_is_ignored(self):
        self.assertEqual(self.check(UNKNOWN, WOMAN, WOMAN), [])

    def test_none_is_ignored(self):
        self.assertEqual(self.check(None, MAN, MAN, MAN), [])

    def test_unavoidable_when_only_one_in_cohort(self):
        violations = self.check(WOMAN, MAN, MAN, MAN)
        self.assertTrue(violations[0].is_unavoidable)
        self.assertIn("unavoidable", violations[0].message)

    def test_avoidable_when_others_exist_elsewhere(self):
        teams = [
            make_team("Team 1", WOMAN, MAN, MAN, MAN),
            make_team("Team 2", WOMAN, MAN, MAN, MAN),
        ]
        violations = self.policy.evaluate(teams)
        self.assertEqual(len(violations), 2)
        self.assertFalse(violations[0].is_unavoidable)

    def test_soft_by_default(self):
        violations = self.check(WOMAN, MAN, MAN, MAN)
        self.assertFalse(violations[0].is_hard)
