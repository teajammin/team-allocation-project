from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


def move_students_to_cohorts(apps, schema_editor):
    Project = apps.get_model('allocations', 'Project')
    Cohort = apps.get_model('allocations', 'Cohort')
    Student = apps.get_model('allocations', 'Student')
    alias = schema_editor.connection.alias
    for project in Project.objects.using(alias).all().iterator():
        cohort = Cohort.objects.using(alias).create(
            project_id=project.pk, name='Initial upload',
        )
        Student.objects.using(alias).filter(project_id=project.pk).update(cohort_id=cohort.pk)


class Migration(migrations.Migration):
    dependencies = [
        ('allocations', '0002_project_allocationrun_student'),
    ]

    operations = [
        migrations.AddField(
            model_name='project', name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='project', name='owner',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name='projects', to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name='Cohort',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cohorts', to='allocations.project')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('project', 'name'), name='unique_cohort_name_per_project')],
            },
        ),
        migrations.AddField(
            model_name='student', name='cohort',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='students', to='allocations.cohort'),
        ),
        # Existing GUI installations retain their imported students. Reversing
        # this data transformation is intentionally unsupported: later cohorts
        # may contain the same email and cannot fit the old project constraint.
        migrations.RunPython(move_students_to_cohorts),
        migrations.RemoveConstraint(
            model_name='student', name='unique_student_email_per_project',
        ),
        migrations.RemoveField(model_name='student', name='project'),
        migrations.AlterField(
            model_name='student', name='cohort',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='students', to='allocations.cohort'),
        ),
        migrations.AddConstraint(
            model_name='student',
            constraint=models.UniqueConstraint(fields=('cohort', 'email'), name='unique_student_email_per_cohort'),
        ),
        migrations.AlterField(
            model_name='student', name='gender',
            field=models.CharField(blank=True, null=True, max_length=1, choices=[('1', 'Woman'), ('2', 'Man'), ('3', 'Other/Non-binary')]),
        ),
        migrations.AlterField(
            model_name='student', name='ethnicity',
            field=models.CharField(blank=True, null=True, max_length=1, choices=[('1', 'Asian or Asian British'), ('2', 'Black, Black British, Caribbean or African'), ('3', 'Mixed or multiple ethnic groups'), ('4', 'White'), ('5', 'Other ethnic group')]),
        ),
        migrations.AlterField(
            model_name='student', name='c_score',
            field=models.PositiveSmallIntegerField(blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)]),
        ),
    ]
