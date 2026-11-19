from collections import Counter

from .base import Policy, Violation

WOMAN = "1"
MAN = "2"
OTHER = "3"

LABELS = {
    WOMAN: "woman",
    MAN: "man",
    OTHER: "non-binary or other student",
}


class GenderPolicy(Policy):
    name = "Gender representation"

    def evaluate(self, teams):
        violations = []
        for team in teams:
            counts = Counter(
                student.gender
                for student in team.students
                if student.gender is not None
            )
            for gender, count in counts.items():
                if count != 1:
                    continue
                if gender == OTHER and self._rest_of_team_is_diverse(counts):
                    continue
                label = LABELS.get(gender, f"student of gender {gender}")
                violations.append(Violation(
                    policy_name=self.name,
                    team_name=team.name,
                    message=f"{team.name} has only one {label}",
                    is_hard=self.is_hard,
                ))
        return violations

    @staticmethod
    def _rest_of_team_is_diverse(counts):
        other_genders = [g for g in counts if g != OTHER]
        return len(other_genders) >= 2
