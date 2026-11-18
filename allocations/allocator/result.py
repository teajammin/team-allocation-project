"""The outcome of an allocation run."""

from enum import Enum

class Status(Enum):
    """The three possible outcomes of an allocation run."""

    SUCCESS = "success"
    INFEASIBLE = "infeasible"
    TIMED_OUT = "timed_out"

class AllocationResult:
    """What allocate() hands back: the outcome, the teams and a message"""

    def __init__(self, status, teams, message):
        if status == Status.SUCCESS and teams is None:
            raise ValueError("A successful result must include teams.")
        if status != Status.SUCCESS and teams is not None:
            raise ValueError("Only a successful result can include teams.")
        self.status = status
        self.teams = teams
        self.message = message