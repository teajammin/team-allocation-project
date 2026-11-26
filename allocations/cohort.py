"""Shared CSV validation and registration/marks reconciliation."""

import csv
import io
import re
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction


REQUIRED_COLUMNS = {'first_name', 'last_name', 'email'}
KNOWN_COLUMNS = REQUIRED_COLUMNS | {'gender', 'ethnicity', 'c-score'}
GENDER_VALUES = {'0', '1', '2', '3'}
ETHNICITY_VALUES = {'0', '1', '2', '3', '4', '5'}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024


@dataclass
class CohortImportResult:
    """Student dictionaries to save and mismatch rows for the upload screen.

    Missing marks are warnings, not validation failures. ``marks_only`` rows
    are reported but never included in ``students``. Names come from the
    registration file; emails are matched after strip/casefold normalization.
    """

    students: list[dict]
    registered_without_marks: list[dict]
    marks_only: list[dict]


def _read_rows(upload, required_columns, *, allow_empty=False):
    if getattr(upload, 'size', 0) > MAX_UPLOAD_SIZE:
        raise ValidationError('The CSV must be no larger than 5 MB.')
    raw = upload.read(MAX_UPLOAD_SIZE + 1)
    if len(raw) > MAX_UPLOAD_SIZE:
        raise ValidationError('The CSV must be no larger than 5 MB.')
    try:
        text = raw.decode('utf-8-sig') if isinstance(raw, bytes) else raw.removeprefix('\ufeff')
    except UnicodeDecodeError as error:
        raise ValidationError('The CSV must be encoded as UTF-8.') from error
    if len(text.encode('utf-8')) > MAX_UPLOAD_SIZE:
        raise ValidationError('The CSV must be no larger than 5 MB.')

    try:
        reader = csv.reader(io.StringIO(text, newline=''), strict=True)
        headers = next(reader, None)
        if not headers:
            raise ValidationError('The CSV is empty or has no header row.')
        headers = [header.strip() for header in headers]
        if any(not header for header in headers):
            raise ValidationError('The CSV contains a blank column name.')
        if len(headers) != len(set(headers)):
            raise ValidationError('The CSV contains duplicate column names.')
        missing = required_columns - set(headers)
        if missing:
            raise ValidationError('Missing required columns: ' + ', '.join(sorted(missing)) + '.')
        rows, errors, seen_emails = [], [], set()
        for values in reader:
            line = reader.line_num
            if len(values) != len(headers):
                errors.append(f'Row {line}: expected {len(headers)} columns, got {len(values)}.')
                continue
            row = dict(zip(headers, (value.strip() for value in values)))
            email = row.get('email', '')
            key = email.casefold()
            try:
                validate_email(email)
                if len(email) > 254:
                    raise ValidationError('Email exceeds 254 characters.')
            except ValidationError:
                errors.append(f'Row {line}: email is not valid.')
            if key in seen_emails:
                errors.append(f'Row {line}: email is duplicated ({email}).')
            seen_emails.add(key)
            rows.append((line, row))
        if not rows and not allow_empty:
            errors.append('The CSV must contain at least one student.')
        if errors:
            raise ValidationError(errors)
        return rows
    except csv.Error as error:
        raise ValidationError(f'The CSV could not be parsed: {error}') from error


def _category(row, field, allowed_values, line_number, errors):
    value = row.get(field, '')
    match = re.fullmatch(r'([0-9]+)(?:\s*:.*)?', value)
    if match:
        value = match.group(1)
    if not value or value == '0':
        return None
    if value not in allowed_values:
        errors.append(
            f'Row {line_number}: {field} must be one of '
            f'{", ".join(sorted(allowed_values))}.'
        )
        return None
    return value


def _score(row, line_number, errors):
    value = row.get('c-score', '')
    if not value:
        return None
    if re.fullmatch(r'[0-9]{1,3}', value) is None:
        errors.append(f'Row {line_number}: c-score must be an integer from 0 to 100.')
        return None
    score = int(value)
    if score > 100:
        errors.append(f'Row {line_number}: c-score must be from 0 to 100.')
        return None
    return score


def parse_cohort_csv(upload):
    """Parse the existing single-file format used by the allocation pages."""
    return _parse_registrations(upload, include_scores=True)


def _parse_registrations(upload, *, include_scores=False):
    rows, errors = [], []
    for line, row in _read_rows(upload, REQUIRED_COLUMNS):
        for field in ('first_name', 'last_name'):
            if not row[field]:
                errors.append(f'Row {line}: {field} is required.')
            elif len(row[field]) > 100:
                errors.append(f'Row {line}: {field} exceeds 100 characters.')
        rows.append({
            'first_name': row['first_name'],
            'last_name': row['last_name'],
            'email': row['email'],
            'gender': _category(row, 'gender', GENDER_VALUES, line, errors),
            'ethnicity': _category(row, 'ethnicity', ETHNICITY_VALUES, line, errors),
            'c_score': _score(row, line, errors) if include_scores else None,
            'extra': {key: value for key, value in row.items() if key not in KNOWN_COLUMNS and value},
        })
    if errors:
        raise ValidationError(errors)
    return rows


def parse_marks_csv(upload):
    """Read marks rows; a header-only file means nobody has marks yet."""
    rows, errors = [], []
    for line, row in _read_rows(upload, {'name', 'email', 'c-score'}, allow_empty=True):
        if not row['name']:
            errors.append(f'Row {line}: name is required.')
        rows.append({'name': row['name'], 'email': row['email'], 'c_score': _score(row, line, errors)})
    if errors:
        raise ValidationError(errors)
    return rows


def parse_two_file_cohort(registrations_file, marks_file):
    """Join registrations to marks by email, retaining only registered people.

    Raises ValidationError for invalid input; no database writes occur here.
    A blank score or absent marks row produces c_score=None and a warning.
    A c-score column in the registration file is ignored in this workflow.
    """
    errors = []
    students, marks = [], []
    try:
        students = _parse_registrations(registrations_file)
    except ValidationError as error:
        errors.extend(f'Registrations: {message}' for message in error.messages)
    try:
        marks = parse_marks_csv(marks_file)
    except ValidationError as error:
        errors.extend(f'Marks: {message}' for message in error.messages)
    if errors:
        raise ValidationError(errors)

    marks_by_email = {row['email'].casefold(): row for row in marks}
    registered_emails = {row['email'].casefold() for row in students}
    without_marks = []
    for student in students:
        mark = marks_by_email.get(student['email'].casefold())
        student['c_score'] = mark['c_score'] if mark else None
        if student['c_score'] is None:
            without_marks.append(student.copy())
    marks_only = [row for row in marks if row['email'].casefold() not in registered_emails]
    return CohortImportResult(students, without_marks, marks_only)


def import_two_file_cohort(project, registrations_file, marks_file):
    """Validate both files, atomically replace project students, return report.

    The caller must check project access before invoking this service. Saved
    allocation snapshots are retained. The report can be rendered by the UI.
    """
    from allocations.models import Project, Student

    result = parse_two_file_cohort(registrations_file, marks_file)
    with transaction.atomic():
        Project.objects.select_for_update().get(pk=project.pk)
        project.students.all().delete()
        Student.objects.bulk_create([Student(project=project, **row) for row in result.students])
    return result
