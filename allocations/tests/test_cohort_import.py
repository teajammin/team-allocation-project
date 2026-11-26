from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import SimpleTestCase, TestCase

from allocations.cohort import (
    MAX_UPLOAD_SIZE,
    import_two_file_cohort,
    parse_cohort_csv,
    parse_two_file_cohort,
)
from allocations.models import Project, Student
from allocations.tests.cohort_helpers import csv_upload, marks_upload, reg_upload
from allocations.tests.helpers import create_user


REGISTRATION = {
    'first_name': 'Alice', 'last_name': 'Example', 'email': 'alice@example.org',
    'gender': '1: Woman', 'ethnicity': '4: White',
}
MARK = {'name': 'Example, Alice', 'email': 'alice@example.org', 'c-score': '0'}


class TwoFileParsingTests(SimpleTestCase):
    def parse(self, registrations=None, marks=None):
        return parse_two_file_cohort(
            reg_upload([REGISTRATION] if registrations is None else registrations),
            marks_upload([MARK] if marks is None else marks),
        )

    def test_valid_files_join_by_email_and_preserve_zero(self):
        result = self.parse()
        self.assertEqual(len(result.students), 1)
        self.assertEqual(result.students[0]['first_name'], 'Alice')
        self.assertEqual(result.students[0]['gender'], '1')
        self.assertEqual(result.students[0]['c_score'], 0)
        self.assertEqual(result.registered_without_marks, [])
        self.assertEqual(result.marks_only, [])

    def test_registered_without_marks_is_retained(self):
        result = self.parse(marks=[])
        self.assertEqual(len(result.students), 1)
        self.assertIsNone(result.students[0]['c_score'])
        self.assertEqual(result.registered_without_marks[0]['email'], REGISTRATION['email'])
        self.assertEqual(result.marks_only, [])

    def test_marks_only_is_reported_and_excluded(self):
        result = self.parse(marks=[MARK, dict(MARK, email='outsider@example.org', name='Other, Person')])
        self.assertEqual([row['email'] for row in result.students], [REGISTRATION['email']])
        self.assertEqual(result.marks_only, [
            {'name': 'Other, Person', 'email': 'outsider@example.org', 'c_score': 0},
        ])

    def test_email_matching_ignores_case_and_whitespace(self):
        result = self.parse(marks=[dict(MARK, email=' ALICE@EXAMPLE.ORG ')])
        self.assertEqual(result.students[0]['c_score'], 0)
        self.assertEqual(result.registered_without_marks, [])
        self.assertEqual(result.marks_only, [])

    def test_registration_name_is_authoritative(self):
        result = self.parse(marks=[dict(MARK, name='Different Name')])
        self.assertEqual(result.students[0]['first_name'], 'Alice')
        self.assertEqual(result.students[0]['last_name'], 'Example')

    def test_blank_score_is_reported_as_missing(self):
        result = self.parse(marks=[dict(MARK, **{'c-score': ''})])
        self.assertIsNone(result.students[0]['c_score'])
        self.assertEqual(len(result.registered_without_marks), 1)

    def test_duplicate_email_is_rejected_in_either_file(self):
        for registrations, marks in [
            ([REGISTRATION, dict(REGISTRATION, email='ALICE@example.org')], [MARK]),
            ([REGISTRATION], [MARK, dict(MARK, email='ALICE@example.org')]),
        ]:
            with self.subTest(registrations=registrations, marks=marks):
                with self.assertRaisesMessage(ValidationError, 'email is duplicated'):
                    self.parse(registrations, marks)

    def test_invalid_marks_are_rejected_including_unregistered_rows(self):
        for score in ('101', '-1', '3.5', 'abc'):
            with self.subTest(score=score):
                with self.assertRaisesMessage(ValidationError, 'Marks:'):
                    self.parse(marks=[dict(MARK, email='outsider@example.org', **{'c-score': score})])

    def test_errors_identify_each_file(self):
        with self.assertRaises(ValidationError) as caught:
            self.parse([dict(REGISTRATION, email='bad')], [dict(MARK, email='bad')])
        self.assertTrue(any(message.startswith('Registrations:') for message in caught.exception.messages))
        self.assertTrue(any(message.startswith('Marks:') for message in caught.exception.messages))

    def test_extra_registration_attributes_are_preserved(self):
        registration = csv_upload(
            'first_name,last_name,email,gender,ethnicity,schedule,ambition,c-score\n'
            'Alice,Example,alice@example.org,0,0,1: Yes,2: Meet workload,99\n'
        )
        result = parse_two_file_cohort(registration, marks_upload([MARK]))
        student = result.students[0]
        self.assertEqual(student['extra'], {'schedule': '1: Yes', 'ambition': '2: Meet workload'})
        self.assertIsNone(student['gender'])
        self.assertIsNone(student['ethnicity'])
        self.assertEqual(student['c_score'], 0)

    def test_team_small_samples(self):
        samples = Path(settings.BASE_DIR) / 'sample_data'
        result = parse_two_file_cohort(
            csv_upload((samples / 'registrations_small.csv').read_text()),
            csv_upload((samples / 'marks_small.csv').read_text()),
        )
        self.assertEqual(len(result.students), 12)
        self.assertEqual(len(result.registered_without_marks), 2)
        self.assertEqual(len(result.marks_only), 2)
        self.assertEqual(sum(row['c_score'] is not None for row in result.students), 10)


class SharedCSVValidationTests(SimpleTestCase):
    def test_legacy_single_file_still_parses(self):
        rows = parse_cohort_csv(csv_upload(
            'first_name,last_name,email,gender,ethnicity,c-score,course\n'
            'Alice,Example,alice@example.org,1: Woman,4: White,75,Computing\n'
        ))
        self.assertEqual(rows[0]['c_score'], 75)
        self.assertEqual(rows[0]['extra'], {'course': 'Computing'})

    def test_optional_columns_can_be_absent(self):
        rows = parse_cohort_csv(csv_upload('first_name,last_name,email\nA,B,a@example.org\n'))
        self.assertIsNone(rows[0]['c_score'])
        self.assertIsNone(rows[0]['gender'])

    def test_invalid_csv_is_rejected(self):
        cases = [
            '',
            'first_name,email\nAlice,alice@example.org\n',
            'first_name,last_name,email,email\nA,B,a@example.org,a@example.org\n',
            'first_name,last_name,email\nA,B\n',
            'first_name,last_name,email\n,A,a@example.org\n',
            'first_name,last_name,email,gender\nA,B,a@example.org,9\n',
            'first_name,last_name,email,ethnicity\nA,B,a@example.org,9\n',
            'first_name,last_name,email,c-score\nA,B,a@example.org,101\n',
            'first_name,last_name,email\nA,B,invalid\n',
            'first_name,last_name,email\n"unterminated\n',
        ]
        for text in cases:
            with self.subTest(text=text), self.assertRaises(ValidationError):
                parse_cohort_csv(csv_upload(text))

    def test_invalid_utf8_is_rejected(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        with self.assertRaisesMessage(ValidationError, 'UTF-8'):
            parse_cohort_csv(SimpleUploadedFile('bad.csv', b'\xff'))

    def test_size_limit_is_enforced(self):
        with self.assertRaisesMessage(ValidationError, '5 MB'):
            parse_cohort_csv(csv_upload('x' * (MAX_UPLOAD_SIZE + 1)))


class TwoFileImportTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(owner=create_user(), name='Example')
        self.existing = Student.objects.create(
            project=self.project, first_name='Old', last_name='Student', email='old@example.org',
        )

    def test_valid_import_replaces_students_and_returns_report(self):
        registrations = [REGISTRATION, dict(REGISTRATION, email='missing@example.org')]
        result = import_two_file_cohort(
            self.project, reg_upload(registrations),
            marks_upload([MARK, dict(MARK, email='outsider@example.org')]),
        )
        self.assertEqual(self.project.students.count(), 2)
        self.assertFalse(Student.objects.filter(pk=self.existing.pk).exists())
        self.assertEqual(self.project.students.get(email=REGISTRATION['email']).c_score, 0)
        self.assertIsNone(self.project.students.get(email='missing@example.org').c_score)
        self.assertFalse(self.project.students.filter(email='outsider@example.org').exists())
        self.assertEqual(len(result.registered_without_marks), 1)
        self.assertEqual(len(result.marks_only), 1)

    def test_invalid_input_keeps_existing_students(self):
        with self.assertRaises(ValidationError):
            import_two_file_cohort(
                self.project, reg_upload([REGISTRATION]), marks_upload([dict(MARK, **{'c-score': 'bad'})]),
            )
        self.assertEqual(list(self.project.students.values_list('pk', flat=True)), [self.existing.pk])

    def test_database_failure_rolls_back_deletion(self):
        with patch('allocations.models.Student.objects.bulk_create', side_effect=IntegrityError('failed')):
            with self.assertRaises(IntegrityError):
                import_two_file_cohort(self.project, reg_upload([REGISTRATION]), marks_upload([MARK]))
        self.assertTrue(Student.objects.filter(pk=self.existing.pk).exists())
