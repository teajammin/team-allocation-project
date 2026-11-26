"""The outcome of an allocation run."""

from enum import Enum


class Status(Enum):
    """The three possible outcomes of an allocation run.

    TIMED_OUT means no valid allocation was found in time,
    not that none exists.
    """

    SUCCESS = "success"
    INFEASIBLE = "infeasible"
    TIMED_OUT = "timed_out"


class AllocationResult:
    """What allocate() hands back: the outcome, the teams, a message and any unmet conditions.

    Teams are only present on SUCCESS. Violations explain what the allocation does not satisfy:
    soft conditions on SUCCESS, or the hard conditions still broken on TIMED_OUT.
    """

    def __init__(self, status, teams, message, violations=()):
        if status == Status.SUCCESS and teams is None:
            raise ValueError("A successful result must include teams.")
        if status != Status.SUCCESS and teams is not None:
            raise ValueError("Only a successful result can include teams.")
        self.status = status
        self.teams = teams
        self.message = message
        self.violations = tuple(violations)
