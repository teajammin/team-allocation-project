from types import SimpleNamespace

from django.test import SimpleTestCase

from allocations.policies.base import (
    Policy,
    Violation,
    get_violations,
    hard_violations_found,
)


class FakePolicy(Policy):
    """A stand-in rule that returns whatever violations it is given."""
    name = "Fake"

    def __init__(self, violations, **kwargs):
        super().__init__(**kwargs)
        self.violations = violations

    def evaluate(self, teams):
        return self.violations


def make_violation(is_hard):
    return Violation("Fake", "Team 1", "Something is wrong", is_hard)


TEAMS = [SimpleNamespace(name="Team 1", students=[])]


class HardViolationsFoundTests(SimpleTestCase):
    def test_no_policies(self):
        self.assertFalse(hard_violations_found(TEAMS, []))

    def test_all_rules_pass(self):
        policies = [FakePolicy([], is_hard=True), FakePolicy([])]
        self.assertFalse(hard_violations_found(TEAMS, policies))

    def test_only_soft_rule_broken(self):
        policies = [FakePolicy([make_violation(False)], is_hard=False)]
        self.assertFalse(hard_violations_found(TEAMS, policies))

    def test_hard_rule_broken(self):
        policies = [FakePolicy([make_violation(True)], is_hard=True)]
        self.assertTrue(hard_violations_found(TEAMS, policies))

    def test_hard_passes_soft_broken(self):
        policies = [
            FakePolicy([], is_hard=True),
            FakePolicy([make_violation(False)], is_hard=False),
        ]
        self.assertFalse(hard_violations_found(TEAMS, policies))


class GetViolationsTests(SimpleTestCase):
    def test_no_policies(self):
        self.assertEqual(get_violations(TEAMS, []), [])

    def test_all_rules_pass(self):
        policies = [FakePolicy([]), FakePolicy([])]
        self.assertEqual(get_violations(TEAMS, policies), [])

    def test_combines_violations_from_all_policies(self):
        first = make_violation(True)
        second = make_violation(False)
        third = make_violation(False)
        policies = [FakePolicy([first]), FakePolicy([second, third])]
        self.assertEqual(get_violations(TEAMS, policies), [first, second, third])


class PolicyBaseTests(SimpleTestCase):
    def test_evaluate_must_be_overridden(self):
        with self.assertRaises(NotImplementedError):
            Policy().evaluate(TEAMS)