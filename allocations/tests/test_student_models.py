from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from allocations.models import Project, Student
from allocations.tests.helpers import create_user


class Role1ModelTests(TestCase):

    def setUp(self):
        self.project = Project.objects.create(
            name="Example Project", owner=create_user()
        )

    def test_models_are_related(self):
        student = Student.objects.create(
            project=self.project,
            first_name="Alice",
            last_name="Example",
            email="alice@example.com",
            gender="1",
            ethnicity="2",
            c_score=0,
            extra={"programme": "Computing"}
        )

        self.assertEqual(
            student.project,
            self.project
        )

        self.assertIn(
            student,
            self.project.students.all()
        )

        self.assertEqual(student.c_score, 0)

    def test_undisclosed_values_are_none(self):
        student = Student.objects.create(
            project=self.project,
            first_name="Bob",
            last_name="Example",
            email="bob@example.com"
        )

        student.refresh_from_db()

        self.assertIsNone(student.gender)
        self.assertIsNone(student.ethnicity)
        self.assertIsNone(student.c_score)
        self.assertEqual(student.extra, {})

    def test_gender_three_is_a_valid_code(self):
        student = Student(
            project=self.project,
            first_name="Casey",
            last_name="Example",
            email="casey@example.com",
            gender="3"
        )

        student.full_clean()

        self.assertEqual(
            student.get_gender_display(),
            "Other/Non-binary"
        )

    def test_score_above_100_is_invalid(self):
        student = Student(
            project=self.project,
            first_name="Casey",
            last_name="Example",
            email="casey@example.com",
            c_score=101
        )

        with self.assertRaises(ValidationError):
            student.full_clean()

    def test_duplicate_email_within_project_is_blocked(self):
        Student.objects.create(
            project=self.project,
            first_name="Alice",
            last_name="One",
            email="alice@example.com"
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Student.objects.create(
                    project=self.project,
                    first_name="Alice",
                    last_name="Two",
                    email="alice@example.com"
                )

    def test_same_email_in_another_project_is_allowed(self):
        other_project = Project.objects.create(
            owner=self.project.owner,
            name="Second project"
        )

        for project in (self.project, other_project):
            Student.objects.create(
                project=project,
                first_name="Alice",
                last_name="Example",
                email="alice@example.com"
            )

        self.assertEqual(
            Student.objects.filter(
                email="alice@example.com"
            ).count(),
            2
        )
