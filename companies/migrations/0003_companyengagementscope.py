from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0002_problemstatement'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyEngagementScope',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('benefits_from_student', models.TextField(blank=True, default='')),
                ('has_value_or_research_project', models.BooleanField(default=False)),
                ('time_availability_and_participation', models.TextField(blank=True, default='')),
                ('workplace_has_conditions_for_group', models.BooleanField(default=False)),
                ('meeting_schedule_availability', models.TextField(blank=True, default='')),
                ('subject_code', models.CharField(max_length=20)),
                ('subject_section', models.CharField(default='1', max_length=10)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='engagement_scopes', to='companies.company')),
            ],
            options={'ordering': ('company', 'subject_code', 'subject_section')},
        ),
        migrations.AddConstraint(
            model_name='companyengagementscope',
            constraint=models.UniqueConstraint(fields=('company', 'subject_code', 'subject_section'), name='uniq_company_engagement_company_subject'),
        ),
    ]

