"""Parsing and validation for uploaded student cohort CSV files."""

import csv
import io
import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_email


REQUIRED_COLUMNS = {'first_name', 'last_name', 'email'}
KNOWN_COLUMNS = REQUIRED_COLUMNS | {'gender', 'ethnicity', 'c-score'}
GENDER_VALUES = {'0', '1', '2', '3'}
ETHNICITY_VALUES = {'0', '1', '2', '3', '4', '5'}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024


def parse_cohort_csv(upload):
    """Return validated student dictionaries or raise actionable CSV errors."""
    if upload.size > MAX_UPLOAD_SIZE:
        raise ValidationError('The CSV must be no larger than 5 MB.')
    try:
        text = upload.read().decode('utf-8-sig')
    except UnicodeDecodeError as error:
        raise ValidationError('The CSV must be encoded as UTF-8.') from error

    try:
        reader = csv.DictReader(io.StringIO(text, newline=''))
        if not reader.fieldnames:
            raise ValidationError('The CSV is empty or has no header row.')
        headers = [header.strip() for header in reader.fieldnames]
        if any(not header for header in headers):
            raise ValidationError('The CSV contains a blank column name.')
        if len(headers) != len(set(headers)):
            raise ValidationError('The CSV contains duplicate column names.')
        missing = REQUIRED_COLUMNS - set(headers)
        if missing:
            raise ValidationError(
                'Missing required columns: ' + ', '.join(sorted(missing)) + '.'
            )

        rows = []
        seen_emails = set()
        errors = []
        for line_number, raw in enumerate(reader, start=2):
            if None in raw:
                errors.append(f'Row {line_number}: has more values than the header.')
                continue
            row = {
                (key.strip() if key else key): (value.strip() if value is not None else '')
                for key, value in raw.items()
            }
            if not any(row.values()):
                errors.append(f'Row {line_number}: is blank.')
                continue

            for field in ('first_name', 'last_name', 'email'):
                if not row.get(field):
                    errors.append(f'Row {line_number}: {field} is required.')

            email = row.get('email', '').casefold()
            if email:
                if email in seen_emails:
                    errors.append(f'Row {line_number}: email is duplicated ({row["email"]}).')
                seen_emails.add(email)

            if email:
                try:
                    validate_email(row['email'])
                except ValidationError:
                    errors.append(f'Row {line_number}: email is not valid.')

            record = {
                'first_name': row.get('first_name', ''),
                'last_name': row.get('last_name', ''),
                'email': row.get('email', ''),
                'gender': _category(row, 'gender', GENDER_VALUES, line_number, errors),
                'ethnicity': _category(row, 'ethnicity', ETHNICITY_VALUES, line_number, errors),
                'c_score': _score(row, line_number, errors),
                'extra': {
                    key: value
                    for key, value in row.items()
                    if key not in KNOWN_COLUMNS and value
                },
            }
            rows.append(record)

        if not rows:
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
    try:
        score = int(value)
    except ValueError:
        errors.append(f'Row {line_number}: c-score must be an integer from 0 to 100.')
        return None
    if not 0 <= score <= 100:
        errors.append(f'Row {line_number}: c-score must be from 0 to 100.')
        return None
    return score
