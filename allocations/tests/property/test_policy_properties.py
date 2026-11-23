from types import SimpleNamespace
from django.test import SimpleTestCase
from hypothesis import given, strategies as st
from allocations.allocator.team import Team
from allocations.policies.attainment import AttainmentPolicy
from allocations.policies.base import (Violation, allocation_penalty, hard_violations_found)
from allocations.policies.ethnicity import EthnicityPolicy
from allocations.policies.gender import GenderPolicy
from allocations.policies.same_attribute import SameAttributePolicy
from allocations.policies.team_size import TeamSizePolicy

GENDERS = st.sampled_from([None, "1", "2", "3"])
ETHNICITIES = st.sampled_from([None, "1", "2", "3", "4", "5"])
MARKS = st.one_of(st.none(), st.integers(0, 100))
COURSES = st.sampled_from([None, "Computing", "Maths"])


def make_student(gender, ethnicity, mark, course):
    """student with fields that policies read"""
    return SimpleNamespace(
        gender=gender,
        ethnicity=ethnicity,
        c_score=mark,
        extra={"course": course},
    )


STUDENTS = st.builds(make_student, GENDERS, ETHNICITIES, MARKS, COURSES)
GROUPS = st.lists(st.lists(STUDENTS, max_size=8), max_size=10)


def make_team(group):
    """list of students becomes numbered teams"""
    teams = []
    for number, students in enumerate(group, start=1):
        teams.append(Team(f"Team {number}", students))
    return teams


def soft_policies():
    """Policy that report findings only"""
    return [GenderPolicy(),
            EthnicityPolicy(),
            AttainmentPolicy(max_spread=20),
            SameAttributePolicy(column="course")
            ]


def every_policy():
    """soft policies amd hard team size policy"""
    return soft_policies() + [TeamSizePolicy(min_size=3, max_size=5)]


def sorted_violations(violations):
    """violations put in fixed order and 2 runs get compared"""
    return sorted(violations, key=lambda v: (v.team_name, v.message))


class PolicyGeneratedTest(SimpleTestCase):
    """run all policies on generated teams to see if rules hold"""

    @given(GROUPS)
    def test_policies_return_violations_list(self, groups):
        teams = make_team(groups)
        for policy in every_policy():
            found = policy.evaluate(teams)
            self.assertIsInstance(found, list)
            for violation in found:
                self.assertIsInstance(violation, Violation)

    @given(GROUPS)
    def test_same_in_same_vio(self, groups):
        teams = make_team(groups)
        for policy in every_policy():
            self.assertEqual(policy.evaluate(teams), policy.evaluate(teams))

    @given(GROUPS)
    def test_vio_pt_real_team(self, groups):
        teams = make_team(groups)
        names = [team.name for team in teams]
        for policy in every_policy():
            for violation in policy.evaluate(teams):
                self.assertIn(violation.team_name, names)
                self.assertEqual(violation.is_hard, policy.is_hard)
                self.assertGreater(violation.severity, 0)

    @given(st.lists(st.integers(0, 8), max_size=10))
    def test_undisclosed_student_cause(self, sizes):
        groups = []
        for size in sizes:
            groups.append([make_student(None, None, None, None)] * size)
        teams = make_team(groups)
        for policy in soft_policies():
            self.assertEqual(policy.evaluate(teams), [])

    @given(GROUPS)
    def test_team_s_policy_count_badT(self, groups):
        teams = make_team(groups)
        policy = TeamSizePolicy(min_size=3, max_size=5)
        bad_teams = 0
        for group in groups:
            if len(group) < 3 or len(group) > 5:
                bad_teams += 1
        self.assertEqual(len(policy.evaluate(teams)), bad_teams)
        self.assertEqual(hard_violations_found(teams, [policy]), bad_teams > 0)

    @given(GROUPS)
    def test_soft_policy_no_hard_pen(self, groups):
        teams = make_team(groups)
        pen = allocation_penalty(teams, soft_policies())
        self.assertEqual(pen[0], 0)
        self.assertFalse(hard_violations_found(teams, soft_policies()))
        for amount in pen:
            self.assertGreaterEqual(amount, 0)
