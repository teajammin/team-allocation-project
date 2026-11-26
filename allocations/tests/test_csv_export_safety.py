import csv
import io

from django.test import TestCase
from django.urls import reverse

from allocations.models import AllocationRun, Project
from allocations.tests.helpers import create_user


class CSVExportSafetyTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)
        self.project = Project.objects.create(owner=self.user, name='Export test')

    def export_values(self, values):
        # Build a saved snapshot directly; no allocation algorithm is run.
        run = AllocationRun.objects.create(
            project=self.project, status='success', message='Saved test snapshot',
            min_team_size=1, max_team_size=1, policies={}, violations=[],
            teams=[{
                'name': values[3],
                'students': [dict(zip(('first_name', 'last_name', 'email'), values[:3]))],
            }],
        )
        response = self.client.get(reverse('allocation_export', args=[self.project.pk, run.pk]))
        self.assertEqual(response.status_code, 200)
        rows = list(csv.reader(io.StringIO(response.content.decode())))
        self.assertEqual(rows[0], ['first_name', 'last_name', 'email', 'team'])
        run.refresh_from_db()
        self.assertEqual(run.teams[0]['name'], values[3])
        self.assertEqual(run.teams[0]['students'][0]['first_name'], values[0])
        return rows[1]

    def test_formula_prefixes_are_escaped_in_every_column(self):
        for value in ['=1+1', '+1+1', '-1+1', '@SUM(1)', '  =1+1', '\t=1+1', '\r=1+1', '\n=1+1']:
            with self.subTest(value=value):
                self.assertEqual(self.export_values([value] * 4), ["'" + value] * 4)

    def test_ordinary_text_and_csv_quoting_are_preserved(self):
        values = ['Anne-Marie', 'O\'Brien, "Junior"', 'anne+test@example.org', 'Team A']
        self.assertEqual(self.export_values(values), values)
