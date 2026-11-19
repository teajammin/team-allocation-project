from .base import Policy, Violation


class SameAttributePolicy(Policy):
    name = "Same attribute"

    def __init__(self, column, **kwargs):
        super().__init__(**kwargs)
        self.column = column

    def evaluate(self, teams):
        violations = []
        for team in teams:
            values = set()
            for student in team.students:
                value = (student.extra or {}).get(self.column)
                if value not in (None, ""):
                    values.add(value)
            if len(values) > 1:
                listed = ", ".join(sorted(str(v) for v in values))
                violations.append(Violation(
                    policy_name=self.name,
                    team_name=team.name,
                    message=(
                        f"{team.name} has different {self.column} "
                        f"values: {listed}"
                    ),
                    is_hard=self.is_hard,
                    severity=len(values) - 1,
                ))
        return violations
