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
                                ('area', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subjects', to='subjects.area')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subjects', to='subjects.semesterlevel')),
                ('teacher', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='subjects', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SubjectUnit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('expected_learning', models.TextField(blank=True, null=True)),
                ('unit_hours', models.PositiveIntegerField(blank=True, null=True)),
                ('activities_description', models.TextField(blank=True, null=True)),
                ('evaluation_evidence', models.TextField(blank=True, null=True)),
                ('evidence_detail', models.TextField(blank=True, null=True)),
                ('counterpart_link', models.TextField(blank=True, null=True)),
                ('place_mode_type', models.TextField(blank=True, null=True)),
                ('counterpart_participant_name', models.TextField(blank=True, null=True)),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='units', to='subjects.subject')),
            ],
            options={'ordering': ('subject', 'number')},
        ),
        migrations.AddConstraint(
            model_name='subjectunit',
            constraint=models.CheckConstraint(check=models.Q(('number__gte', 1), ('number__lte', 4)), name='unit_number_between_1_4'),
        ),
        migrations.AddConstraint(
            model_name='subjectunit',
            constraint=models.UniqueConstraint(fields=('subject', 'number'), name='uniq_unit_subject_number'),
        ),
        migrations.CreateModel(
            name='SubjectTechnicalCompetency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('description', models.TextField(blank=True, null=True)),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='technical_competencies', to='subjects.subject')),
            ],
            options={'ordering': ('subject', 'number')},
        ),
        migrations.AddConstraint(
            model_name='subjecttechnicalcompetency',
            constraint=models.CheckConstraint(check=models.Q(('number__gte', 1), ('number__lte', 5)), name='competency_number_between_1_5'),
        ),
        migrations.AddConstraint(
            model_name='subjecttechnicalcompetency',
            constraint=models.UniqueConstraint(fields=('subject', 'number'), name='uniq_competency_subject_number'),
        ),
        migrations.CreateModel(
            name='CompanyBoundaryCondition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('large_company', models.BooleanField(null=True)),
                ('medium_company', models.BooleanField(null=True)),
                ('small_company', models.BooleanField(null=True)),
                ('family_enterprise', models.BooleanField(null=True)),
                ('not_relevant', models.BooleanField(null=True)),
                ('company_type_description', models.TextField(blank=True, null=True)),
                ('company_requirements_for_level_2_3', models.TextField(blank=True, null=True)),
                ('project_minimum_elements', models.TextField(blank=True, null=True)),
                ('subject', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='company_boundary_conditions', to='subjects.subject')),
            ],
            options={'ordering': ('subject',)},
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
        migrations.CreateModel(
            name='CompanyEngagementScope',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('benefits_from_student', models.TextField(blank=True, default='')),
                ('has_value_or_research_project', models.BooleanField(default=False)),
                ('time_availability_and_participation', models.TextField(blank=True, default='')),
                ('workplace_has_conditions_for_group', models.BooleanField(default=False)),
                ('meeting_schedule_availability', models.TextField(blank=True, default='')),
                ('subject', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='engagement_scope', to='subjects.subject')),
            ],
            options={'ordering': ('subject',)},
        ),
        migrations.CreateModel(
            name='ProblemStatement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('problem_to_address', models.TextField(blank=True, default='')),
                ('why_important', models.TextField(blank=True, default='')),
                ('stakeholders', models.TextField(blank=True, default='')),
                ('related_area', models.TextField(blank=True, default='')),
                ('benefits_short_medium_long_term', models.TextField(blank=True, default='')),
                ('problem_definition', models.TextField(blank=True, default='')),
                ('counterpart_contacts', models.JSONField(default=__import__('subjects.models', fromlist=['default_counterpart_contacts']).default_counterpart_contacts)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='problem_statements', to='companies.company')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problem_statements', to='subjects.subject')),
            ],
            options={'ordering': ('subject', 'company')},
        ),
        migrations.AddConstraint(
            model_name='problemstatement',
            constraint=models.UniqueConstraint(fields=('subject', 'company'), name='uniq_problem_statement_subject_company'),
        ),
        migrations.RunPython(seed_areas_and_semesters, migrations.RunPython.noop),
    ]

