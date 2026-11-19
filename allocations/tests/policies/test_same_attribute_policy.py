from types import SimpleNamespace

from django.test import SimpleTestCase

from allocations.policies.same_attribute import SameAttributePolicy


def make_team(name, *values):
    students = [SimpleNamespace(extra={"programme": v}) for v in values]
    return SimpleNamespace(name=name, students=students)


class SameAttributePolicyTests(SimpleTestCase):
    def setUp(self):
        self.policy = SameAttributePolicy(column="programme", priority=4)

    def check(self, *values):
        return self.policy.evaluate([make_team("Team 1", *values)])

    def test_all_same_passes(self):
        self.assertEqual(self.check("CS", "CS", "CS"), [])

    def test_different_values_fail(self):
        violations = self.check("CS", "CS", "Maths")
        self.assertEqual(len(violations), 1)
        self.assertIn("CS, Maths", violations[0].message)

    def test_blank_and_missing_ignored(self):
        self.assertEqual(self.check("CS", "", None, "CS"), [])

    def test_severity_counts_extra_values(self):
        violations = self.check("CS", "Maths", "Physics")
        self.assertEqual(violations[0].severity, 2)

    def test_student_without_extra_data(self):
        team = SimpleNamespace(
            name="Team 1",
            students=[SimpleNamespace(extra=None)],
        )
        self.assertEqual(self.policy.evaluate([team]), [])
