import csv
import io

from django.test import SimpleTestCase, TestCase

from allocations.csv_utils import (
    CSVValidationError,
    export_allocation_csv,
    import_cohort_csv,
    parse_cohort_csv,
)
from allocations.models import Cohort, Project, Student
#for CSV import, validation and export

HEADERS = (
    "first_name,last_name,email,"
    "gender,ethnicity,c-score,"
    "programme,experience\n"
)


def csv_upload(lines):
    content = HEADERS + "\n".join(lines) + "\n"

    return io.BytesIO(
        content.encode("utf-8")
    )


class Role1CSVParsingTests(SimpleTestCase):

    def test_valid_file_preserves_codes_and_extra_attributes(self):
        rows, errors = parse_cohort_csv(
            csv_upload([
                "Alice,Example,alice@example.com,1,2,0,Computing,3",
                "Bob,Example,bob@example.com,0,,75,,",
                "Casey,Example,casey@example.com,3,5,100,Maths,1"
            ])
        )

        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 3)

        self.assertEqual(rows[0]["gender"], "1")
        self.assertEqual(rows[0]["c_score"], 0)

        self.assertEqual(
            rows[0]["extra"]["programme"],
            "Computing"
        )

        self.assertIsNone(rows[1]["gender"])
        self.assertIsNone(rows[1]["ethnicity"])
        self.assertIsNone(rows[1]["extra"]["experience"])

        self.assertEqual(rows[2]["gender"], "3")

    def test_optional_columns_can_be_absent(self):
        file = io.BytesIO(
            b"first_name,last_name,email\n"
            b"Alice,Example,alice@example.com\n"
        )

        rows, errors = parse_cohort_csv(file)

        self.assertEqual(errors, [])
        self.assertIsNone(rows[0]["c_score"])
        self.assertEqual(rows[0]["extra"], {})

    def test_missing_required_header_is_rejected(self):
        file = io.BytesIO(
            b"first_name,email\n"
            b"Alice,alice@example.com\n"
        )

        rows, errors = parse_cohort_csv(file)

        self.assertEqual(rows, [])
        self.assertIn("last_name", errors[0])

    def test_unexpected_gender_is_rejected(self):
        rows, errors = parse_cohort_csv(
            csv_upload([
                "Alice,Example,alice@example.com,9,2,80,Computing,3"
            ])
        )

        self.assertEqual(rows, [])
        self.assertIn("gender", errors[0])

    def test_unexpected_ethnicity_is_rejected(self):
        rows, errors = parse_cohort_csv(
            csv_upload([
                "Alice,Example,alice@example.com,1,9,80,Computing,3"
            ])
        )

        self.assertEqual(rows, [])
        self.assertIn("ethnicity", errors[0])

    def test_out_of_range_c_score_is_rejected(self):
        rows, errors = parse_cohort_csv(
            csv_upload([
                "Alice,Example,alice@example.com,1,2,101,Computing,3"
            ])
        )

        self.assertEqual(rows, [])
        self.assertIn("c-score", errors[0])

    def test_decimal_c_score_is_rejected(self):
        rows, errors = parse_cohort_csv(
            csv_upload([
                "Alice,Example,alice@example.com,1,2,70.5,Computing,3"
            ])
        )

        self.assertEqual(rows, [])
        self.assertIn("integer", errors[0])

    def test_duplicate_email_case_insensitive_is_rejected(self):
        rows, errors = parse_cohort_csv(
            csv_upload([
                "Alice,Example,alice@example.com,1,2,75,Computing,3",
                "Alice,Two,ALICE@example.com,2,3,65,Maths,1"
            ])
        )

        self.assertEqual(rows, [])

        self.assertIn(
            "duplicate student email",
            errors[0]
        )

    def test_bad_row_does_not_produce_partial_result(self):
        rows, errors = parse_cohort_csv(
            csv_upload([
                "Alice,Example,alice@example.com,1,2,75,Computing,3",
                "Bob,Example,bob@example.com,2,1,not-a-number,Maths,1"
            ])
        )

        self.assertEqual(rows, [])
        self.assertTrue(errors)

    def test_malformed_column_count_is_rejected(self):
        rows, errors = parse_cohort_csv(
            csv_upload([
                "Alice,Example,alice@example.com,1,2,75"
            ])
        )

        self.assertEqual(rows, [])
        self.assertIn("expected", errors[0])

    def test_invalid_utf8_is_rejected(self):
        rows, errors = parse_cohort_csv(
            io.BytesIO(b"\xff\xfe")
        )

        self.assertEqual(rows, [])
        self.assertIn("UTF-8", errors[0])

    def test_empty_file_is_rejected(self):
        rows, errors = parse_cohort_csv(
            io.BytesIO(b"")
        )

        self.assertEqual(rows, [])
        self.assertTrue(errors)


class Role1CSVDatabaseTests(TestCase):

    def setUp(self):
        self.project = Project.objects.create(
            name="Project One"
        )

        self.cohort = Cohort.objects.create(
            project=self.project,
            name="Cohort One"
        )

    def create_student(self, email, first_name="Alice"):
        return Student.objects.create(
            cohort=self.cohort,
            first_name=first_name,
            last_name="Example",
            email=email,
            gender="1",
            ethnicity="2",
            c_score=0
        )

    def test_import_saves_valid_rows(self):
        count, errors = import_cohort_csv(
            csv_upload([
                "Alice,Example,alice@example.com,1,2,0,Computing,3",
                "Bob,Example,bob@example.com,0,0,,Maths,1"
            ]),
            self.cohort
        )

        self.assertEqual((count, errors), (2, []))

        bob = Student.objects.get(
            email="bob@example.com"
        )

        self.assertIsNone(bob.gender)
        self.assertIsNone(bob.ethnicity)
        self.assertIsNone(bob.c_score)

    def test_invalid_import_does_not_save_any_student(self):
        count, errors = import_cohort_csv(
            csv_upload([
                "Alice,Example,alice@example.com,1,2,0,Computing,3",
                "Bob,Example,bob@example.com,5,0,12,Maths,1"
            ]),
            self.cohort
        )

        self.assertEqual(count, 0)
        self.assertTrue(errors)

        self.assertEqual(
            Student.objects.count(),
            0
        )

    def test_existing_email_does_not_allow_partial_import(self):
        self.create_student("alice@example.com")

        count, errors = import_cohort_csv(
            csv_upload([
                "Bob,Example,bob@example.com,1,2,90,Computing,3",
                "Alice,Another,ALICE@example.com,2,3,80,Maths,1"
            ]),
            self.cohort
        )

        self.assertEqual(count, 0)
        self.assertTrue(errors)

        self.assertEqual(
            Student.objects.count(),
            1
        )

    def test_export_has_exactly_four_columns(self):
        alice = self.create_student(
            "alice@example.com"
        )

        bob = self.create_student(
            "bob@example.com",
            "Bob"
        )

        content = export_allocation_csv(
            self.cohort,
            [
                (alice, "Team A"),
                (bob, "Team B")
            ]
        )

        reader = csv.DictReader(
            io.StringIO(content)
        )

        self.assertEqual(
            reader.fieldnames,
            [
                "first_name",
                "last_name",
                "email",
                "team"
            ]
        )

        rows = list(reader)

        self.assertEqual(len(rows), 2)

        self.assertEqual(
            {row["team"] for row in rows},
            {"Team A", "Team B"}
        )

    def test_export_rejects_missing_student(self):
        alice = self.create_student(
            "alice@example.com"
        )

        self.create_student(
            "bob@example.com",
            "Bob"
        )

        with self.assertRaises(CSVValidationError):
            export_allocation_csv(
                self.cohort,
                [(alice, "Team A")]
            )

    def test_export_rejects_duplicate_student(self):
        alice = self.create_student(
            "alice@example.com"
        )

        with self.assertRaises(CSVValidationError):
            export_allocation_csv(
                self.cohort,
                [
                    (alice, "Team A"),
                    (alice, "Team B")
                ]
            )

    def test_export_rejects_out_of_cohort_student(self):
        other_cohort = Cohort.objects.create(
            project=self.project,
            name="Other"
        )

        outsider = Student.objects.create(
            cohort=other_cohort,
            first_name="Bob",
            last_name="Example",
            email="bob@example.com"
        )

        self.create_student(
            "alice@example.com"
        )

        with self.assertRaises(CSVValidationError):
            export_allocation_csv(
                self.cohort,
                [(outsider, "Team A")]
            )
