from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('allocations', '0002_project_allocationrun_student')]

    operations = [
        migrations.AlterField(
            model_name='student', name='gender',
            field=models.CharField(
                blank=True, null=True, max_length=1,
                choices=[('1', 'Woman'), ('2', 'Man'), ('3', 'Other/Non-binary')],
            ),
        ),
        migrations.AlterField(
            model_name='student', name='ethnicity',
            field=models.CharField(
                blank=True, null=True, max_length=1,
                choices=[
                    ('1', 'Asian or Asian British'),
                    ('2', 'Black, Black British, Caribbean or African'),
                    ('3', 'Mixed or multiple ethnic groups'),
                    ('4', 'White'), ('5', 'Other ethnic group'),
                ],
            ),
        ),
        migrations.AlterField(
            model_name='student', name='c_score',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)],
            ),
        ),
    ]
