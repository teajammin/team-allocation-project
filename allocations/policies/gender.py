from collections import Counter

from .base import Policy, Violation

UNKNOWN = "0"
WOMAN = "1"
MAN = "2"
NON_BINARY = "3"

GENDER_LABELS = {WOMAN: "woman", MAN: "man"}


class GenderPolicy(Policy):
    name = "Gender representation"

    def evaluate(self, teams):
        total_counts = Counter(
            student.gender for team in teams for student in team.students
        )
        violations = []
        for team in teams:
            counts = Counter(
                student.gender
                for student in team.students
                if student.gender in GENDER_LABELS
            )
            for gender, count in counts.items():
                if count != 1:
                    continue
                label = GENDER_LABELS[gender]
                is_unavoidable = total_counts[gender] == 1
                message = f"{team.name} has only one {label}"
                if is_unavoidable:
                    message += f" (unavoidable: only one {label} in the cohort)"
                violations.append(Violation(
                    policy_name=self.name,
                    team_name=team.name,
                    is_hard=self.is_hard,
                    message=message,
                    is_unavoidable=is_unavoidable,
                ))
        return violations
