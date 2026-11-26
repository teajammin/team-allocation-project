from django.test import SimpleTestCase

from allocations.allocator.result import AllocationResult, Status
from allocations.allocator.team import Team
from allocations.policies.base import Violation

TEAMS = [Team("Team 1", ["amy", "ben", "cara", "dan"])]
LONE_WOMAN = Violation("Gender representation", "Team 1", "Team 1 has only one woman", is_hard=False)


class AllocationResultTestCase(SimpleTestCase):

    def test_success_keeps_its_teams(self):
        result = AllocationResult(Status.SUCCESS, TEAMS, "1 team made.")
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertEqual(result.teams, TEAMS)

    def test_success_without_teams_is_rejected(self):
        with self.assertRaises(ValueError):
            AllocationResult(Status.SUCCESS, None, "No teams.")

    def test_unsuccessful_outcomes_have_no_teams(self):
        for status in (Status.INFEASIBLE, Status.TIMED_OUT):
            with self.subTest(status=status):
                result = AllocationResult(status, None, "No allocation.")
                self.assertIsNone(result.teams)

    def test_unsuccessful_outcomes_with_teams_are_rejected(self):
        for status in (Status.INFEASIBLE, Status.TIMED_OUT):
            with self.subTest(status=status):
                with self.assertRaises(ValueError):
                    AllocationResult(status, TEAMS, "No allocation.")

    def test_violations_default_to_none(self):
        result = AllocationResult(Status.SUCCESS, TEAMS, "1 team made.")
        self.assertEqual(result.violations, ())

    def test_status_reports_unmet_soft_conditions(self):
        result = AllocationResult(Status.SUCCESS, TEAMS, "1 team made.", [LONE_WOMAN])
        self.assertEqual(result.violations, (LONE_WOMAN,))

    def test_timed_out_reports_remaining_problems_without_teams(self):
        result = AllocationResult(Status.TIMED_OUT, None, "Out of time.", [LONE_WOMAN])
        self.assertIsNone(result.teams)
        self.assertEqual(result.violations, (LONE_WOMAN,))

    def test_later_changes_to_the_list_do_not_change_the_result(self):
        violations = [LONE_WOMAN]
        result = AllocationResult(Status.SUCCESS, TEAMS, "1 team made.", violations)
        violations.clear()
        self.assertEqual(result.violations, (LONE_WOMAN,))
