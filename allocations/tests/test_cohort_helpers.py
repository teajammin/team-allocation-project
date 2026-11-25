import csv
import io
from django.test import SimpleTestCase
from allocations.tests.cohort_helpers import (csv_upload,
                                              marks_upload,
                                              reg_upload,
                                              to_csv)


class HelperTests(SimpleTestCase):
    """check the helpers that build CSV yploads for the other tests"""

    def test_upload_text_and_name(self):
        upload = csv_upload('a,b\n1,2\n', 'people.csv')
        self.assertEqual(upload.name, 'people.csv')
        self.assertEqual(upload.read().decode('utf-8'), 'a,b\n1,2\n')

    def test_commas_round_trip(self):
        rows = [{'label': '1: Asian, or Asian British'}]
        text = to_csv(['label'], rows)
        read_back = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual(read_back, rows)

    def test_reg_header(self):
        upload = reg_upload([{'first_name': 'Ann', 'email': 'a@b.org'}])
        text = upload.read().decode('utf-8')
        self.assertTrue(text.startswith('first_name,last_name,email'))

    def test_marks_header(self):
        upload = marks_upload(
            [{'name': 'Ann Lee',
              'email': 'ann@exmaple.org', 'c-score': 50}])
        text = upload.read().decode('utf-8')
        self.assertTrue(text.startswith('name,email,c-score'))
