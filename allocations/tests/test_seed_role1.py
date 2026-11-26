from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from allocations.models import Project, Student


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

    def test_existing_passwords_and_permissions_are_preserved(self):
        user_model = get_user_model()
        existing = []
        for username, staff, superuser in [('janedoe', False, False), ('johndoe', True, True)]:
            user = user_model.objects.create_user(
                username=username, password='Existing-secret-123',
                email=f'{username}@custom.example', first_name='Custom', last_name='Name',
                is_staff=staff, is_superuser=superuser,
            )
            existing.append((user, user.password, staff, superuser))

        call_command('seed_role1', verbosity=0)

        for user, password_hash, staff, superuser in existing:
            user.refresh_from_db()
            self.assertEqual(user.password, password_hash)
            self.assertEqual(user.is_staff, staff)
            self.assertEqual(user.is_superuser, superuser)
            self.assertEqual(user.email, f'{user.username}@custom.example')
            self.assertEqual(user.first_name, 'Custom')
