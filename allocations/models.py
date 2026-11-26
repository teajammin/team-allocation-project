from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class User(AbstractUser):
    """A user of the group allocation application.

    AbstractUser already provides username, first_name, last_name, email,
    password and is_superuser (amongst others). We redefine first_name,
    last_name and email so that they are required, and so that no two users
    can share an email address.
    """

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.get_full_name()} ({self.username})'


class Project(models.Model):
    """A staff-managed allocation project and its current student cohort."""

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name', 'id']

    def __str__(self):
        return self.name


class Student(models.Model):
    """A student in a project's imported cohort."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='students')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    gender = models.CharField(
        max_length=1, blank=True, null=True,
        choices=[('1', 'Woman'), ('2', 'Man'), ('3', 'Other/Non-binary')],
    )
    ethnicity = models.CharField(
        max_length=1, blank=True, null=True,
        choices=[
            ('1', 'Asian or Asian British'),
            ('2', 'Black, Black British, Caribbean or African'),
            ('3', 'Mixed or multiple ethnic groups'),
            ('4', 'White'), ('5', 'Other ethnic group'),
        ],
    )
    c_score = models.PositiveSmallIntegerField(
        blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name', 'email']
        constraints = [
            models.UniqueConstraint(fields=['project', 'email'], name='unique_student_email_per_project'),
        ]

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.email})'


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
