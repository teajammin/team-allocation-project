from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from allocations.models import Project, Student


# Seed users and synthetic data for the allocation system.
class Command(BaseCommand):
    help = "Seed required users and sample cohort data."

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed_users()

        self._seed_cohort(
            "Software Engineering Group Work",
            120,
            0
        )

        self._seed_cohort(
            "Data Science Group Work",
            60,
            1000
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Role 1 users and cohorts seeded."
            )
        )

    def _seed_users(self):
        user_model = get_user_model()

        users = (
            ("janedoe", "Jane", "Doe", True, True),
            ("johndoe", "John", "Doe", False, False),
        )

        for username, first_name, last_name, is_staff, is_superuser in users:
            user, created = user_model.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": f"{username}@example.com",
                    "is_staff": is_staff,
                    "is_superuser": is_superuser
                }
            )

            if created:
                user.set_password("Allocation123")
                user.save(update_fields=["password"])

    def _seed_cohort(
        self,
        project_name,
        count,
        offset
    ):
        project, _ = Project.objects.get_or_create(
            name=project_name,
            owner=get_user_model().objects.get(username="janedoe"),
        )

        for index in range(1, count + 1):
            number = index + offset

            gender = (
                "1", "2", "3", None
            )[number % 4]

            ethnicity = (
                "1", "2", "3", "4", "5", None
            )[number % 6]

            Student.objects.get_or_create(
                project=project,
                email=f"student{number:04d}@example.com",
                defaults={
                    "first_name": f"Student{number:04d}",
                    "last_name": "Example",
                    "gender": gender,
                    "ethnicity": ethnicity,
                    "c_score": number % 101,
                    "extra": {
                        "programme": (
                            "Computing"
                            if number % 2
                            else "Mathematics"
                        ),
                        "experience": str(number % 4)
                    }
                }
            )
