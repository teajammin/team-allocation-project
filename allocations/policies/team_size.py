from .base import Policy, Violation


class TeamSizePolicy(Policy):
    name = "Team size"

    def __init__(self, min_size, max_size, is_hard=True, priority=None):
        super().__init__(is_hard=is_hard, priority=priority)
        self.min_size = min_size
        self.max_size = max_size

    def evaluate(self, teams):
        violations = []
        for team in teams:
            size = len(team.students)
            if size < self.min_size or size > self.max_size:
                violations.append(Violation(
                                    policy_name=self.name, 
                                    team_name=team.name, 
                                    message=(
                                        f"{team.name} has {size} students "
                                        f"(allowed {self.min_size}-{self.max_size})"), 
                                    is_hard=self.is_hard
                                   ))
        return violations