# Group Allocation system by Team *seals*
A group allocation system developed for the Small Group Project assignment of the Software Engineering Group Project module at King's College London.

## Team members
The members of the team are:
- Thea Zeitoun
- Adna Ali
- Faysal Abdallah
- Xiangyu Song
- Adam Ansari


## Deployment

The system has been deployed at [https://seals.pythonanywhere.com](https://seals.pythonanywhere.com)


## Getting started

```
python3.12 -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed             # Adds sample users
python manage.py runserver
```

Then open <http://127.0.0.1:8000/> and log in as `janedoe` (a superuser) or
`johndoe` (a normal user). Both have the password `Allocation123`.

Run `python manage.py unseed` to delete all users again.

## Projects and allocations

After logging in, open **Projects** from the dashboard to create a project and
upload its cohort. Cohort files must be UTF-8 CSVs no larger than 5 MB and must
contain `first_name`, `last_name` and `email` columns. The optional columns
`gender`, `ethnicity` and `c-score` are validated against the categories and
score range in the assignment; additional columns are retained as student
attributes. Email addresses must be unique within a cohort (case-insensitive).
Uploads are rejected in full if any row is invalid; replacing a cohort leaves
existing allocation-run snapshots intact.

Allocation runs use the configured minimum and maximum team sizes and call
`allocate(students, policies)` as implemented. The current allocator uses
`c-score` to order students while forming teams and only enforces team-size
limits. Optional gender and attainment checks are evaluated after allocation
and reported as findings; they do not influence team formation or guarantee a
policy-compliant allocation. The attainment check requires a c-score for every
student. Infeasible runs are saved for inspection but cannot be exported.

Successful runs can be inspected and exported as CSV with exactly these
columns, in order: `first_name`, `last_name`, `email`, `team`.

## Tests

Run all tests with `python manage.py test`. You can also run a part of them,
for example `python manage.py test allocations.tests.views`. 

[Coverage.py](https://coverage.readthedocs.io/) measures which parts of the
code the tests run. Its settings are in `.coveragerc`.

```
coverage run manage.py test       # Run the tests while measuring coverage
coverage report                   # Show the coverage of each file
coverage html                     # Write a detailed report to htmlcov/
```

Open `htmlcov/index.html` in a browser to see exactly which lines and
branches are not tested. The report leaves out code that is not ours or that
is not worth testing, such as the virtual environment, migrations, settings
and the tests themselves.

## Two-file import service

`allocations.cohort.parse_two_file_cohort(registrations_file, marks_file)`
validates both CSV files and returns a `CohortImportResult` with:

- `students`: registered student dictionaries ready for `Student(project=..., **row)`.
- `registered_without_marks`: registered students whose score is missing (`None`).
- `marks_only`: marks rows without a matching registration, excluded from students.

Registrations require `first_name,last_name,email`; gender and ethnicity are
optional, and additional attributes such as schedule and ambition are retained
in `extra`. Marks require `name,email,c-score`. Emails are matched ignoring case
and surrounding whitespace. Registration names are authoritative. Blank scores
and header-only marks files are allowed; zero is a valid score. In the two-file
workflow, scores come only from the marks file. Invalid files raise Django
`ValidationError` with the file type and row details where available.

`import_two_file_cohort(project, registrations_file, marks_file)` validates first,
then replaces the project's students in a transaction and returns the same
report. The caller must enforce project permissions. Allocation snapshots remain
unchanged. The upload UI can render the two mismatch lists; the existing single
CSV forms remain compatible until the two-file screen is connected.

Apply migrations with `python manage.py migrate`. Migration 0003 adds model
validation while retaining the existing Project/Student schema and nullable
scores. Seed sample projects with `python manage.py seed_role1`.

Run the relevant tests and lint checks with:

```sh
python manage.py test allocations.tests.test_cohort_import allocations.tests.test_student_models allocations.tests.test_seed_role1 allocations.tests.test_allocation_workflow
python manage.py makemigrations --check --dry-run
python -m flake8
```
