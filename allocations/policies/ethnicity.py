from collections import Counter

from .base import Policy, Violation

LABELS = {
    "1": "Asian or Asian British student",
    "2": "Black, Black British, Caribbean or African student",
    "3": "student of mixed or multiple ethnic groups",
    "4": "White student",
    "5": "student of another ethnic group",
}


class EthnicityPolicy(Policy):
    name = "Ethnicity diversity"

    def evaluate(self, teams):
        violations = []
        for team in teams:
            counts = Counter(
                student.ethnicity
                for student in team.students
                if student.ethnicity is not None
            )
            for ethnicity, count in counts.items():
                if count == 1:
                    label = LABELS.get(
                        ethnicity, f"student of ethnicity {ethnicity}"
                    )
                    violations.append(Violation(
                        policy_name=self.name,
                        team_name=team.name,
                        message=f"{team.name} has only one {label}",
                        is_hard=self.is_hard,
                    ))
        return violations
