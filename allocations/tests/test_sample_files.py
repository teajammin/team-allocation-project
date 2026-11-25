import csv
from django.conf import settings
from django.test import SimpleTestCase

SAMPLES = settings.BASE_DIR / 'sample_data'
REG_COLUMNS = ['first_name', 'last_name', 'email', 'gender',
               'ethnicity', 'schedule', 'ambition']
MARKS_COLUMNS = ['name', 'email', 'c-score']
EXPORT_COLUMNS = ['first_name', 'last_name', 'email', 'team']


def read_rows(file_name):
    """read a sample CSV to a list of dictionaries"""
    with open(SAMPLES / file_name, newline='', encoding='utf-8') as file:
        return list(csv.DictReader(file))


def email_set(rows):
    """emails in a file in lower case to compare"""
    return {row['email'].strip().casefold() for row in rows}


def code_of(value):
    """number before colon"""
    return value.split(':')[0].strip()


class RealFilesTest(SimpleTestCase):
    def setUp(self):
        self.reg = read_rows('sample_registrations_file.csv')
        self.marks = read_rows('sample_marks_file.csv')

    def test_300_rows(self):
        self.assertEqual(len(self.reg), 300)
        self.assertEqual(len(self.marks), 300)

    def test_columns(self):
        self.assertEqual(list(self.reg[0]), REG_COLUMNS)
        self.assertEqual(list(self.marks[0]), MARKS_COLUMNS)

    def test_all_match(self):
        self.assertEqual(email_set(self.reg), email_set(self.marks))

    def test_marks_names(self):
        for row in self.marks:
            self.assertIn(', ', row['name'])


class RealValuesTest(SimpleTestCase):
    def setUp(self):
        self.reg = read_rows('sample_registrations_file.csv')
        self.marks = read_rows('sample_marks_file.csv')

    def count(self, column, value):
        """the amount of registrations have this value"""
        return len([row for row in self.reg if row[column] == value])

    def test_scores(self):
        for row in self.marks:
            self.assertTrue(0 <= int(row['c-score']) <= 100)

    def test_gender_codes(self):
        for row in self.reg:
            self.assertIn(code_of(row['gender']), ['0', '1', '2', '3'])

    def test_ethnicity_codes(self):
        for row in self.reg:
            self.assertIn(code_of(row['ethnicity']), list('012345'))

    def test_first_row(self):
        first = self.reg[0]
        self.assertEqual(first['first_name'], 'Rahul')
        self.assertEqual(first['last_name'], 'Khan')
        self.assertEqual(first['gender'], '2: Man')
        self.assertEqual(self.marks[0]['name'], 'Khan, Rahul')
        self.assertEqual(self.marks[0]['c-score'], '57')

    def test_last_row(self):
        last = self.reg[-1]
        self.assertEqual(last['last_name'], 'Darwish')
        self.assertEqual(last['ethnicity'], '0')
        self.assertEqual(self.marks[-1]['c-score'], '73')

    def test_not_provided(self):
        self.assertEqual(self.count('gender', '0'), 15)
        self.assertEqual(self.count('ethnicity', '0'), 27)
        self.assertEqual(self.count('ambition', '0'), 3)


class SmallFilesTest(SimpleTestCase):
    """small thing with mismatches created"""
    def setUp(self):
        self.reg = read_rows('registrations_small.csv')
        self.marks = read_rows('marks_small.csv')

    def test_unique(self):
        for row in (self.reg, self.marks):
            self.assertEqual(len(email_set(row)), len(row))

    def test_overlap(self):
        registered = email_set(self.reg)
        marked = email_set(self.marks)
        self.assertEqual(len(registered & marked), 10)
        self.assertEqual(len(registered - marked), 2)
        self.assertEqual(len(marked - registered), 2)

    def test_case_email(self):
        exact = {row['email'] for row in self.reg}
        lower = email_set(self.reg)
        found = []
        for row in self.marks:
            email = row['email']
            if email not in exact and email.strip().casefold() in lower:
                found.append(email)
        self.assertEqual(found, ['RAMI.FAHMY@students.example'])


class ExportFileTest(SimpleTestCase):
    """example export file"""
    def setUp(self):
        self.export = read_rows('sample_allocation_data.csv')
        self.reg = read_rows('sample_registrations_file.csv')

    def test_columns(self):
        self.assertEqual(list(self.export[0]), EXPORT_COLUMNS)

    def test_registered(self):
        self.assertTrue(email_set(self.export) <= email_set(self.reg))

    def test_once(self):
        emails = [row['email'] for row in self.export]
        self.assertEqual(len(emails), len(set(emails)))

    def test_sizes(self):
        sizes = {}
        for row in self.export:
            sizes[row['team']] = sizes.get(row['team'], 0) + 1
        for size in sizes.values():
            self.assertTrue(4 <= size <= 5)
