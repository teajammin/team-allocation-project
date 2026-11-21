from collections import Counter

from .base import Policy, Violation

UNKNOWN = "0"

ETHNICITY_LABELS = {
    "1": "Asian or Asian British student",
    "2": "Black, Black British, Caribbean or African student",
    "3": "student of mixed or multiple ethnic groups",
    "4": "White student",
    "5": "student of another ethnic group",
}


class EthnicityPolicy(Policy):
    name = "Ethnicity diversity"

    def evaluate(self, teams):
        total_counts = Counter(
            student.ethnicity for team in teams for student in team.students
        )
        violations = []
        for team in teams:
            counts = Counter(
                student.ethnicity
                for student in team.students
                if student.ethnicity in ETHNICITY_LABELS
            )
            for ethnicity, count in counts.items():
                if count != 1:
                    continue
                label = ETHNICITY_LABELS[ethnicity]
                is_unavoidable = total_counts[ethnicity] == 1
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
