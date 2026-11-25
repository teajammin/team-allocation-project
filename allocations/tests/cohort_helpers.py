import csv
import io
from django.core.files.uploadedfile import SimpleUploadedFile


def csv_upload(text, name='cohorts.csv'):
    """make the CSV text an uploaded file"""
    return SimpleUploadedFile(name, text.encode('utf-8'), content_type='text/csv')


def to_csv(columns, rows):
    """list of row dictionaries becomes a CSV text"""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def reg_upload(rows):
    """uploaded registration file created from row dictionaries"""
    columns = ['first_name', 'last_name', 'email', 'gender', 'ethnicity']
    return csv_upload(to_csv(columns, rows), 'registrations.csv')


def marks_upload(rows):
    """uploaded marks file created from row dictionaries"""
    columns = ['name', 'email', 'c-score']
    return csv_upload(to_csv(columns, rows), 'marks.csv')
