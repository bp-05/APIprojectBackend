from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


AREAS = [
    "Administración",
    "Agroindustria Y Medioambiente",
    "Automatización, Electrónica Y Robótica",
    "Construcción",
    "Diseño E Industria Digital",
    "Energía",
    "Gastronomía",
    "Informática, Ciberseguridad Y Telecomunicaciones",
    "Logística",
    "Mecánica",
    "Minería",
    "Salud",
    "Turismo Y Hospitalidad",
]

SEMESTERS = [
    "Primero",
    "Segundo",
    "Tercero",
    "Cuarto",
    "Quinto",
    "Sexto",
    "Septimo",
    "Octavo",
    "Noveno",
    "Decimo",
]


def seed_areas_and_semesters(apps, schema_editor):
    Area = apps.get_model('subjects', 'Area')
    SemesterLevel = apps.get_model('subjects', 'SemesterLevel')
    for name in AREAS:
        Area.objects.get_or_create(name=name)
    for name in SEMESTERS:
        SemesterLevel.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('companies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
            options={'ordering': ('name',)},
        ),
        migrations.CreateModel(
            name='SemesterLevel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True)),
            ],
            options={'ordering': ('id',)},
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('campus', models.CharField(default='chillan', max_length=50)),
                ('hours', models.PositiveIntegerField(default=0)),
                ('api_type', models.PositiveSmallIntegerField(choices=((1, 'Type 1'), (2, 'Type 2'), (3, 'Type 3')), default=1)),
                ('units', models.JSONField(default=__import__('subjects.models', fromlist=['default_subject_units']).default_subject_units)),
                ('technical_competencies', models.JSONField(default=__import__('subjects.models', fromlist=['default_subject_competencies']).default_subject_competencies)),
                ('company_boundary_conditions', models.JSONField(default=__import__('subjects.models', fromlist=['default_company_boundary_conditions']).default_company_boundary_conditions)),
                                ('area', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subjects', to='subjects.area')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subjects', to='subjects.semesterlevel')),
                ('teacher', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='subjects', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CompanyRequirement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sector', models.CharField(max_length=100)),
                ('worked_before', models.BooleanField(default=False)),
                ('interest_collaborate', models.BooleanField(default=False)),
                ('can_develop_activities', models.BooleanField(default=False)),
                ('willing_design_project', models.BooleanField(default=False)),
                ('interaction_type', models.CharField(choices=(('virtual', 'Virtual'), ('onsite_company', 'On-site at company'), ('onsite_inacap', 'On-site at INACAP')), default='virtual', max_length=20)),
                ('has_guide', models.BooleanField(default=False)),
                ('can_receive_alternance', models.BooleanField(default=False)),
                ('alternance_students_quota', models.PositiveIntegerField(default=0)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='requirements', to='companies.company')),
                ('subject', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='company_requirement', to='subjects.subject')),
            ],
            options={'ordering': ('subject',)},
        ),
        migrations.CreateModel(
            name='Api3Alternance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_role', models.CharField(max_length=200)),
                ('students_quota', models.PositiveIntegerField(default=0)),
                ('tutor_name', models.CharField(max_length=200)),
                ('tutor_email', models.EmailField(max_length=254)),
                ('alternance_hours', models.PositiveIntegerField(default=0)),
                ('subject', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='alternance', to='subjects.subject')),
            ],
            options={'ordering': ('subject',)},
        ),
        migrations.CreateModel(
            name='ApiType2Completion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_goal_students', models.TextField(blank=True, default='')),
                ('deliverables_at_end', models.TextField(blank=True, default='')),
                ('company_expected_participation', models.TextField(blank=True, default='')),
                ('other_activities', models.TextField(blank=True, default='')),
                ('subject', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='api2_completion', to='subjects.subject')),
            ],
            options={'ordering': ('subject',)},
        ),
        migrations.CreateModel(
            name='ApiType3Completion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_goal_students', models.TextField(blank=True, default='')),
                ('deliverables_at_end', models.TextField(blank=True, default='')),
                ('expected_student_role', models.TextField(blank=True, default='')),
                ('other_activities', models.TextField(blank=True, default='')),
                ('master_guide_expected_support', models.TextField(blank=True, default='')),
                ('subject', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='api3_completion', to='subjects.subject')),
            ],
            options={'ordering': ('subject',)},
        ),
        migrations.RunPython(seed_areas_and_semesters, migrations.RunPython.noop),
    ]

