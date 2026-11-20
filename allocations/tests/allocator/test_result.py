from django.test import SimpleTestCase

from allocations.allocator.result import AllocationResult, Status
from allocations.allocator.team import Team


class AllocationResultTestCase(SimpleTestCase):

    def test_success_keeps_its_teams(self):
        teams = [Team("Team 1", ["amy", "ben", "cara", "dan"])]
        result = AllocationResult(Status.SUCCESS, teams, "1 team made.")
        self.assertEqual(result.status, Status.SUCCESS)
        self.assertEqual(result.teams, teams)

    def test_success_without_teams_is_rejected(self):
        with self.assertRaises(ValueError):
            AllocationResult(Status.SUCCESS, None, "No teams.")

    def test_failure_with_teams_is_rejected(self):
        teams = [Team("Team 1", ["amy", "ben", "cara", "dan"])]
        with self.assertRaises(ValueError):
            AllocationResult(Status.INFEASIBLE, teams, "Impossible.")
