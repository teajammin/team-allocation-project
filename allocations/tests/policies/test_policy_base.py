from types import SimpleNamespace

from django.test import SimpleTestCase

from allocations.policies.base import (
    Policy,
    Violation,
    allocation_penalty,
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


class AllocationPenaltyTests(SimpleTestCase):
    def test_no_violations_scores_zero(self):
        policies = [FakePolicy([], is_hard=True), FakePolicy([], priority=1)]
        self.assertEqual(allocation_penalty(TEAMS, policies), (0, 0))

    def test_hard_violation_counts_first(self):
        policies = [FakePolicy([make_violation(True)], is_hard=True)]
        self.assertEqual(allocation_penalty(TEAMS, policies), (1,))

    def test_soft_totals_ordered_by_priority(self):
        policies = [
            FakePolicy([make_violation(False)] * 3, priority=2),
            FakePolicy([make_violation(False)], priority=1),
        ]
        self.assertEqual(allocation_penalty(TEAMS, policies), (0, 1, 3))

    def test_severity_is_added_up(self):
        heavy = Violation("Fake", "Team 1", "Way over", False, severity=7)
        policies = [FakePolicy([heavy], priority=1)]
        self.assertEqual(allocation_penalty(TEAMS, policies), (0, 7))

    def test_higher_priority_problem_outweighs_many_lower(self):
        fewer_p1 = (0, 1, 9)
        more_p1 = (0, 2, 5)
        self.assertLess(fewer_p1, more_p1)

    def test_any_hard_problem_is_worse_than_soft_ones(self):
        self.assertLess((0, 50, 50), (1, 0, 0))

    def test_missing_priority_counts_last(self):
        policies = [
            FakePolicy([make_violation(False)], priority=None),
            FakePolicy([make_violation(False)] * 2, priority=1),
        ]
        self.assertEqual(allocation_penalty(TEAMS, policies), (0, 2, 1))
