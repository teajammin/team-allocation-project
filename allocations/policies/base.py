from dataclasses import dataclass


@dataclass
class Violation:
    policy_name: str
    team_name: str
    message: str
    is_hard: bool
    severity: float = 1


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


def allocation_penalty(teams, policies):
    hard_total = 0
    soft_totals = {}
    for policy in policies:
        amount = sum(v.severity for v in policy.evaluate(teams))
        if policy.is_hard:
            hard_total += amount
        else:
            priority = policy.priority if policy.priority is not None else 99
            soft_totals[priority] = soft_totals.get(priority, 0) + amount
    ordered = [soft_totals[p] for p in sorted(soft_totals)]
    return (hard_total, *ordered)
