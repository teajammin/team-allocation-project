from dataclasses import dataclass


@dataclass
class Violation:
    policy_name: str
    team_name: str
    message: str
    is_hard: bool


class Policy:
    name = "Policy"

    def __init__(self, is_hard=False, priority=None):
        self.is_hard = is_hard
        self.priority = priority

    def evaluate(self, teams):
        raise NotImplementedError


def hard_violations_found(teams, policies):
    for policy in policies:
        if policy.is_hard and policy.evaluate(teams):
            return True
    return False


def get_violations(teams, policies):
    violations = []
    for policy in policies:
        violations.extend(policy.evaluate(teams))
    return violations