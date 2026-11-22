from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class User(AbstractUser):
    """A user of the group allocation application."""

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"


class Project(models.Model):
    """A project requiring students to be allocated to teams."""

    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="projects",
        null=True, blank=True,
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "id"]

    @property
    def current_cohort(self):
        """Use the latest imported batch for the project allocation pages."""
        return self.cohorts.order_by("-uploaded_at", "-pk").first()

    @property
    def students(self):
        """Expose students from the current batch without mixing cohorts."""
        cohort = self.current_cohort
        return cohort.students.all() if cohort else Student.objects.none()

    def __str__(self):
        return self.name


class Cohort(models.Model):
    """A cohort of students belonging to a project."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="cohorts"
    )

    name = models.CharField(max_length=150)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"],
                name="unique_cohort_name_per_project"
            )
        ]

    def __str__(self):
        return f"{self.project.name}: {self.name}"


class Student(models.Model):
    """A student belonging to an imported cohort."""

    GENDER_CHOICES = [
        ("1", "Woman"),
        ("2", "Man"),
        ("3", "Other/Non-binary"),
    ]

    ETHNICITY_CHOICES = [
        ("1", "Asian or Asian British"),
        ("2", "Black, Black British, Caribbean or African"),
        ("3", "Mixed or multiple ethnic groups"),
        ("4", "White"),
        ("5", "Other ethnic group"),
    ]

    cohort = models.ForeignKey(
        Cohort,
        on_delete=models.CASCADE,
        related_name="students"
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)

    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        null=True,
        blank=True
    )

    ethnicity = models.CharField(
        max_length=1,
        choices=ETHNICITY_CHOICES,
        null=True,
        blank=True
    )

    c_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )

    extra = models.JSONField(
        default=dict,
        blank=True
    )

    class Meta:
        ordering = ["last_name", "first_name", "email"]

        constraints = [
            models.UniqueConstraint(
                fields=["cohort", "email"],
                name="unique_student_email_per_cohort"
            )
        ]

    def __str__(self):
        return (
            f"{self.first_name} "
            f"{self.last_name} ({self.email})"
        )


class AllocationRun(models.Model):
    """A saved outcome and snapshot of one allocation attempt."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='allocation_runs')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)
    message = models.CharField(max_length=300)
    min_team_size = models.PositiveSmallIntegerField()
    max_team_size = models.PositiveSmallIntegerField()
    policies = models.JSONField(default=dict)
    teams = models.JSONField(default=list)
    violations = models.JSONField(default=list)

    class Meta:
        ordering = ['-created_at', '-id']
