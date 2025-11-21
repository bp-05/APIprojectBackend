from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial'),
        ('subjects', '0001_initial'),
    ]

    operations = [
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
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='problem_statements', to='companies.company')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problem_statements', to='subjects.subject')),
            ],
            options={'ordering': ('subject', 'company')},
        ),
        migrations.CreateModel(
            name='CounterpartContact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, default='', max_length=255)),
                ('rut', models.CharField(blank=True, default='', max_length=50)),
                ('phone', models.CharField(blank=True, default='', max_length=50)),
                ('email', models.EmailField(blank=True, default='', max_length=254)),
                ('counterpart_area', models.CharField(blank=True, default='', max_length=255)),
                ('role', models.CharField(blank=True, default='', max_length=255)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='counterpart_contacts', to='companies.company')),
            ],
            options={'ordering': ('company', 'id')},
        ),
    ]
