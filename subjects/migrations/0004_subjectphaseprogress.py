from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('subjects', '0003_companyengagementscope'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubjectPhaseProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phase', models.CharField(
                    max_length=20,
                    choices=[
                        ('formulacion', 'Formulación'),
                        ('gestion', 'Gestión'),
                        ('validacion', 'Validación'),
                    ],
                )),
                ('status', models.CharField(
                    max_length=2,
                    choices=[
                        ('nr', 'No realizado'),
                        ('ec', 'En curso'),
                        ('rz', 'Realizado'),
                    ],
                    default='nr',
                )),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('notes', models.TextField(blank=True, default='')),
                ('subject', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='phase_progress',
                    to='subjects.subject',
                )),
                ('updated_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='phase_progress_updates',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ('subject', 'phase'),
                'verbose_name': 'Progreso de Fase',
                'verbose_name_plural': 'Progresos de Fases',
            },
        ),
        migrations.AddConstraint(
            model_name='subjectphaseprogress',
            constraint=models.UniqueConstraint(
                fields=('subject', 'phase'),
                name='unique_subject_phase',
            ),
        ),
    ]
