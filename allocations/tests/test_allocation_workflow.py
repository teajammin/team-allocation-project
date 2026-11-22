import csv
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from allocations.models import AllocationRun, Cohort, Project, Student
from allocations.tests.helpers import create_user


def cohort_csv(count=8):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['first_name', 'last_name', 'email', 'gender', 'ethnicity', 'c-score', 'course'])
    for number in range(count):
        writer.writerow([
            f'Student{number}',
            'Example',
            f'student{number}@example.org',
            str(number % 2 + 1),
            str(number % 3 + 1),
            number * 10,
            'Computing',
        ])
    return output.getvalue().encode()


class AllocationWorkflowTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        self.project = Project.objects.create(owner=self.user, name='Software Engineering')
        self.cohort = Cohort.objects.create(project=self.project, name='Initial upload')

    def upload(self, content):
        return SimpleUploadedFile('cohort.csv', content, content_type='text/csv')

    def test_project_creation_imports_valid_cohort(self):
        response = self.client.post(reverse('project_create'), {
            'name': 'New project',
            'cohort_file': self.upload(cohort_csv()),
        })

        project = Project.objects.get(name='New project')
        self.assertRedirects(response, reverse('project_detail', args=[project.id]))
        self.assertEqual(project.students.count(), 8)
        student = project.students.get(email='student0@example.org')
        self.assertEqual(student.c_score, 0)
        self.assertEqual(student.extra, {'course': 'Computing'})

    def test_project_import_accepts_assignment_labeled_categories(self):
        sample_rows = (
            b'first_name,last_name,email,gender,ethnicity,c-score\n'
            b'Rahul,Khan,rahul@example.org,2: Man,"1: Asian, or Asian British",57\n'
            b'Rami,Fahmy,rami@example.org,2: Man,5 : Other ethnic group (e.g. Arab),63\n'
            b'Victoria,Thomas,victoria@example.org,1: Woman,4: White,66\n'
            b'Zoya,Banerjee,zoya@example.org,1: Woman,"3 : Mixed, or multiple ethic groups",46\n'
        )

        response = self.client.post(reverse('project_create'), {
            'name': 'Sample format project',
            'cohort_file': self.upload(sample_rows),
        })

        project = Project.objects.get(name='Sample format project')
        self.assertRedirects(response, reverse('project_detail', args=[project.id]))
        self.assertEqual(
            list(project.students.order_by('email').values_list('gender', flat=True)),
            ['2', '2', '1', '1'],
        )
        self.assertEqual(
            list(project.students.order_by('email').values_list('ethnicity', flat=True)),
            ['1', '5', '4', '3'],
        )

    def test_invalid_cohort_is_not_imported(self):
        invalid_csv = (
            b'first_name,last_name,email,gender,ethnicity,c-score\n'
            b'Alice,Example,alice@example.org,9,1,25\n'
        )
        response = self.client.post(reverse('project_create'), {
            'name': 'Invalid project',
            'cohort_file': self.upload(invalid_csv),
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'gender must be one of')
        self.assertFalse(Project.objects.filter(name='Invalid project').exists())

    def test_duplicate_email_addresses_are_rejected_case_insensitively(self):
        duplicate_csv = (
            b'first_name,last_name,email\n'
            b'Alice,Example,alice@example.org\n'
            b'Alice,Example,ALICE@example.org\n'
        )
        response = self.client.post(reverse('project_create'), {
            'name': 'Duplicate cohort',
            'cohort_file': self.upload(duplicate_csv),
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'email is duplicated')
        self.assertFalse(Project.objects.filter(name='Duplicate cohort').exists())

    def test_cohort_replacement_is_atomic_on_invalid_upload(self):
        Student.objects.create(
            cohort=self.cohort,
            first_name='Existing',
            last_name='Student',
            email='existing@example.org',
        )
        response = self.client.post(
            reverse('cohort_upload', args=[self.project.id]),
            {'cohort_file': self.upload(b'first_name,last_name\nMissing,Email\n')},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Missing required columns')
        self.assertEqual(list(self.project.students.values_list('email', flat=True)), [
            'existing@example.org',
        ])

    def test_allocation_run_displays_teams_and_exports_required_columns(self):
        for number in range(8):
            Student.objects.create(
                cohort=self.cohort,
                first_name=f'Student{number}',
                last_name='Example',
                email=f'student{number}@example.org',
                gender=str(number % 2 + 1),
                c_score=number * 10,
            )

        response = self.client.post(reverse('allocation_create', args=[self.project.id]), {
            'min_team_size': 4,
            'max_team_size': 4,
            'check_gender': 'on',
            'check_attainment': 'on',
            'max_spread': 20,
        })

        allocation_run = AllocationRun.objects.get(project=self.project)
        self.assertRedirects(
            response,
            reverse('allocation_run_detail', args=[self.project.id, allocation_run.id]),
        )
        self.assertEqual(allocation_run.status, 'success')
        self.assertEqual(len(allocation_run.teams), 2)
        self.assertTrue(allocation_run.violations)

        detail = self.client.get(response.url)
        self.assertContains(detail, 'were not optimization constraints')

        export = self.client.get(reverse(
            'allocation_export',
            args=[self.project.id, allocation_run.id],
        ))
        rows = list(csv.reader(io.StringIO(export.content.decode())))
        self.assertEqual(rows[0], ['first_name', 'last_name', 'email', 'team'])
        self.assertEqual(len(rows), 9)

    def test_infeasible_result_is_saved_but_not_exported(self):
        for number in range(7):
            Student.objects.create(
                cohort=self.cohort,
                first_name=f'Student{number}',
                last_name='Example',
                email=f'student{number}@example.org',
            )

        self.client.post(reverse('allocation_create', args=[self.project.id]), {
            'min_team_size': 4,
            'max_team_size': 5,
        })
        allocation_run = AllocationRun.objects.get(project=self.project)
        self.assertEqual(allocation_run.status, 'infeasible')
        self.assertEqual(allocation_run.teams, [])
        export = self.client.get(reverse(
            'allocation_export',
            args=[self.project.id, allocation_run.id],
        ))
        self.assertRedirects(
            export,
            reverse('allocation_run_detail', args=[self.project.id, allocation_run.id]),
        )

    def test_attainment_check_requires_a_score_for_every_student(self):
        Student.objects.create(
            cohort=self.cohort,
            first_name='Student',
            last_name='Example',
            email='student@example.org',
        )

        response = self.client.post(reverse('allocation_create', args=[self.project.id]), {
            'min_team_size': 1,
            'max_team_size': 1,
            'check_attainment': 'on',
            'max_spread': 20,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'requires a c-score for every student')
        self.assertFalse(AllocationRun.objects.filter(project=self.project).exists())

    def test_users_cannot_access_another_users_project(self):
        other_user = create_user('anotheruser')
        other_project = Project.objects.create(owner=other_user, name='Private project')

        response = self.client.get(reverse('project_detail', args=[other_project.id]))

        self.assertEqual(response.status_code, 404)

    def test_valid_upload_preserves_previous_cohort(self):
        original = Student.objects.create(
            cohort=self.cohort, first_name='Previous', last_name='Student',
            email='previous@example.org',
        )
        response = self.client.post(
            reverse('cohort_upload', args=[self.project.id]),
            {'cohort_file': self.upload(cohort_csv())},
        )
        self.assertRedirects(response, reverse('project_detail', args=[self.project.id]))
        self.assertEqual(self.project.cohorts.count(), 2)
        self.assertTrue(self.cohort.students.filter(pk=original.pk).exists())
        self.assertEqual(self.project.students.count(), 8)
        self.assertFalse(self.project.students.filter(pk=original.pk).exists())
