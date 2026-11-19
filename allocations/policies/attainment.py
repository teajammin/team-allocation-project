from .base import Policy, Violation


class AttainmentPolicy(Policy):
    name = "Prior attainment"

    def __init__(self, max_spread, **kwargs):
        super().__init__(**kwargs)
        self.max_spread = max_spread

    def evaluate(self, teams):
        violations = []
        for team in teams:
            scores = [
                student.c_score
                for student in team.students
                if student.c_score is not None
            ]
            if len(scores) < 2:
                continue
            spread = max(scores) - min(scores)
            if spread > self.max_spread:
                violations.append(Violation(
                    policy_name=self.name,
                    team_name=team.name,
                    message=(
                        f"{team.name} has a mark spread of {spread:g} "
                        f"(target {self.max_spread:g} or less)"
                    ),
                    is_hard=self.is_hard,
                    severity=spread - self.max_spread,
                ))
        return violations
