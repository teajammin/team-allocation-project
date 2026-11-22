from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from allocations.models import Cohort, Project, Student
#for the seed command.

class Role1SeedCommandTests(TestCase):

    def test_seed_creates_required_users_and_data(self):
        call_command(
            "seed_role1",
            verbosity=0
        )

        user_model = get_user_model()

        admin = user_model.objects.get(
            username="janedoe"
        )

        regular = user_model.objects.get(
            username="johndoe"
        )

        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)

        self.assertFalse(regular.is_superuser)

        self.assertTrue(
            admin.check_password("Allocation123")
        )

        self.assertTrue(
            regular.check_password("Allocation123")
        )

        self.assertEqual(Project.objects.count(), 2)
        self.assertEqual(Cohort.objects.count(), 2)
        self.assertEqual(Student.objects.count(), 180)

    def test_seed_is_idempotent(self):
        call_command(
            "seed_role1",
            verbosity=0
        )

        call_command(
            "seed_role1",
            verbosity=0
        )

        self.assertEqual(
            Student.objects.count(),
            180
        )

        self.assertEqual(
            Project.objects.count(),
            2
        )

        self.assertEqual(
            Cohort.objects.count(),
            2
        )

    def test_seed_includes_undisclosed_and_other_gender(self):
        call_command(
            "seed_role1",
            verbosity=0
        )

        self.assertTrue(
            Student.objects.filter(
                gender__isnull=True
            ).exists()
        )

        self.assertTrue(
            Student.objects.filter(
                gender="3"
            ).exists()
        )

        self.assertTrue(
            Student.objects.filter(
                ethnicity__isnull=True
            ).exists()
        )
