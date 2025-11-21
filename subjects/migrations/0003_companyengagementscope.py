from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0002_periodsetting_defaults'),
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
                ('subject', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='engagement_scope', to='subjects.subject')),
            ],
            options={'ordering': ('subject',)},
        ),
    ]
