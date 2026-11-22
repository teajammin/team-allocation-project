import csv
import io
import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction

from allocations.models import Student
#for csv parser and validator and csv export


REQUIRED_HEADERS = (
    "first_name",
    "last_name",
    "email"
)

OPTIONAL_HEADERS = (
    "gender",
    "ethnicity",
    "c-score"
)

OUTPUT_HEADERS = (
    "first_name",
    "last_name",
    "email",
    "team"
)

VALID_GENDERS = frozenset({"1", "2", "3"})

VALID_ETHNICITIES = frozenset({
    "1", "2", "3", "4", "5"
})

MAX_FILE_BYTES = 5 * 1024 * 1024


class CSVValidationError(ValueError):
    """Raised when a CSV file contains invalid data."""


def parse_category(value, allowed_codes, field_name):
    """Convert undisclosed values to None."""

    raw = "" if value is None else str(value).strip()

    if raw in {"", "0"}:
        return None

    if raw not in allowed_codes:
        raise CSVValidationError(
            f"{field_name} has invalid code {raw!r}."
        )

    return raw


def parse_c_score(value):
    """Validate a C-score between 0 and 100."""

    raw = "" if value is None else str(value).strip()

    if not raw:
        return None

    if re.fullmatch(r"[0-9]+", raw) is None:
        raise CSVValidationError(
            "c-score must be an integer between 0 and 100."
        )

    score = int(raw)

    if score > 100:
        raise CSVValidationError(
            "c-score must be between 0 and 100."
        )

    return score


def _decode_csv(uploaded_file):
    """Decode a UTF-8 CSV file with a 5 MB size limit."""

    if getattr(uploaded_file, "size", 0) > MAX_FILE_BYTES:
        raise CSVValidationError(
            "The CSV is larger than the 5 MB upload limit."
        )

    raw = uploaded_file.read(MAX_FILE_BYTES + 1)

    if len(raw) > MAX_FILE_BYTES:
        raise CSVValidationError(
            "The CSV is larger than the 5 MB upload limit."
        )

    if isinstance(raw, bytes):
        try:
            return raw.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise CSVValidationError(
                "The CSV must use UTF-8 encoding."
            ) from error

    if not isinstance(raw, str):
        raise CSVValidationError(
            "Uploaded data is not a text or binary CSV file."
        )

    return raw.removeprefix("\ufeff")


def _headers_from(reader):
    """Read and validate CSV column names."""

    try:
        raw_headers = next(reader)
    except StopIteration as error:
        raise CSVValidationError(
            "The CSV is empty."
        ) from error

    headers = [
        header.strip()
        for header in raw_headers
    ]

    if any(not header for header in headers):
        raise CSVValidationError(
            "The CSV has an unnamed column."
        )

    if len(headers) != len(set(headers)):
        raise CSVValidationError(
            "The CSV has duplicate column names."
        )

    missing = sorted(
        set(REQUIRED_HEADERS) - set(headers)
    )

    if missing:
        raise CSVValidationError(
            "Missing required columns: "
            + ", ".join(missing)
        )

    return headers


def _validate_student_row(headers, values, line_number):
    """Validate and convert one student record."""

    if len(values) != len(headers):
        raise CSVValidationError(
            f"Row {line_number}: expected "
            f"{len(headers)} columns, got {len(values)}."
        )

    row = dict(zip(headers, values))

    first_name = row["first_name"].strip()
    last_name = row["last_name"].strip()
    email = row["email"].strip()

    if not first_name or not last_name or not email:
        raise CSVValidationError(
            f"Row {line_number}: first_name, "
            "last_name and email are required."
        )

    if len(first_name) > 100 or len(last_name) > 100:
        raise CSVValidationError(
            f"Row {line_number}: a name exceeds 100 characters."
        )

    if len(email) > 254:
        raise CSVValidationError(
            f"Row {line_number}: email exceeds 254 characters."
        )

    try:
        validate_email(email)
    except ValidationError as error:
        raise CSVValidationError(
            f"Row {line_number}: invalid email {email!r}."
        ) from error

    try:
        gender = parse_category(
            row.get("gender"),
            VALID_GENDERS,
            "gender"
        )

        ethnicity = parse_category(
            row.get("ethnicity"),
            VALID_ETHNICITIES,
            "ethnicity"
        )

        c_score = parse_c_score(
            row.get("c-score")
        )

    except CSVValidationError as error:
        raise CSVValidationError(
            f"Row {line_number}: {error}"
        ) from error

    extra = {
        key: (value.strip() or None)
        for key, value in row.items()
        if key not in REQUIRED_HEADERS + OPTIONAL_HEADERS
    }

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "gender": gender,
        "ethnicity": ethnicity,
        "c_score": c_score,
        "extra": extra
    }


def parse_cohort_csv(uploaded_file):
    """Return validated student rows and any errors."""

    try:
        text = _decode_csv(uploaded_file)

        reader = csv.reader(
            io.StringIO(text, newline=""),
            strict=True
        )

        headers = _headers_from(reader)

    except (CSVValidationError, csv.Error) as error:
        return [], [str(error)]

    rows = []
    errors = []
    emails_seen = set()

    try:
        for values in reader:
            line_number = reader.line_num

            try:
                student = _validate_student_row(
                    headers,
                    values,
                    line_number
                )

                email_key = student["email"].casefold()

                if email_key in emails_seen:
                    raise CSVValidationError(
                        f"Row {line_number}: duplicate "
                        f"student email {student['email']!r}."
                    )

                emails_seen.add(email_key)
                rows.append(student)

            except CSVValidationError as error:
                errors.append(str(error))

    except csv.Error as error:
        errors.append(
            f"Malformed CSV near line "
            f"{reader.line_num}: {error}"
        )

    if not rows and not errors:
        errors.append(
            "The CSV contains no student records."
        )

    if errors:
        return [], errors

    return rows, []


@transaction.atomic
def import_cohort_csv(uploaded_file, cohort):
    """Import all valid students or save none."""

    rows, errors = parse_cohort_csv(uploaded_file)

    if errors:
        return 0, errors

    existing_emails = {
        email.casefold()
        for email in Student.objects.filter(
            cohort=cohort
        ).values_list("email", flat=True)
    }

    duplicated = sorted({
        row["email"]
        for row in rows
        if row["email"].casefold() in existing_emails
    })

    if duplicated:
        return 0, [
            "Email already exists in this cohort: "
            + ", ".join(duplicated)
        ]

    students = [
        Student(cohort=cohort, **row)
        for row in rows
    ]

    Student.objects.bulk_create(students)

    return len(rows), []


def export_allocation_csv(cohort, assignments):
    """Export all students and their assigned teams."""

    students = {
        student.pk: student
        for student in cohort.students.all()
    }

    if not students:
        raise CSVValidationError(
            "Cannot export an empty cohort allocation."
        )

    teams_by_student_id = {}

    for student, team_name in assignments:
        student_id = (
            student.pk
            if isinstance(student, Student)
            else student
        )

        if student_id not in students:
            raise CSVValidationError(
                f"Student {student_id!r} is not in this cohort."
            )

        if student_id in teams_by_student_id:
            raise CSVValidationError(
                f"Student {student_id!r} "
                "has multiple team assignments."
            )

        if not isinstance(team_name, str) or not team_name.strip():
            raise CSVValidationError(
                f"Student {student_id!r} "
                "has no valid team name."
            )

        teams_by_student_id[student_id] = team_name.strip()

    missing = (
        students.keys()
        - teams_by_student_id.keys()
    )

    if missing:
        raise CSVValidationError(
            f"{len(missing)} students "
            "are not assigned to a team."
        )

    output = io.StringIO(newline="")
    writer = csv.writer(output)

    writer.writerow(OUTPUT_HEADERS)

    ordered_students = sorted(
        students.values(),
        key=lambda item: item.email.casefold()
    )

    for student in ordered_students:
        writer.writerow([
            student.first_name,
            student.last_name,
            student.email,
            teams_by_student_id[student.pk]
        ])

    return output.getvalue()
