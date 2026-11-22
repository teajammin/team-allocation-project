
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from allocations.models import Cohort, Project, Student
#for  database models.

class Role1ModelTests(TestCase):

    def setUp(self):
        self.project = Project.objects.create(
            name="Example Project"
        )

        self.cohort = Cohort.objects.create(
            project=self.project,
            name="First upload"
        )

    def test_models_are_related(self):
        student = Student.objects.create(
            cohort=self.cohort,
            first_name="Alice",
            last_name="Example",
            email="alice@example.com",
            gender="1",
            ethnicity="2",
            c_score=0,
            extra={"programme": "Computing"}
        )

        self.assertEqual(
            student.cohort.project,
            self.project
        )

        self.assertIn(
            student,
            self.cohort.students.all()
        )

        self.assertEqual(student.c_score, 0)

    def test_undisclosed_values_are_none(self):
        student = Student.objects.create(
            cohort=self.cohort,
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
            cohort=self.cohort,
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
            cohort=self.cohort,
            first_name="Casey",
            last_name="Example",
            email="casey@example.com",
            c_score=101
        )

        with self.assertRaises(ValidationError):
            student.full_clean()

    def test_duplicate_email_within_cohort_is_blocked(self):
        Student.objects.create(
            cohort=self.cohort,
            first_name="Alice",
            last_name="One",
            email="alice@example.com"
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Student.objects.create(
                    cohort=self.cohort,
                    first_name="Alice",
                    last_name="Two",
                    email="alice@example.com"
                )

    def test_same_email_in_another_cohort_is_allowed(self):
        other_cohort = Cohort.objects.create(
            project=self.project,
            name="Second upload"
        )

        for cohort in (self.cohort, other_cohort):
            Student.objects.create(
                cohort=cohort,
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
