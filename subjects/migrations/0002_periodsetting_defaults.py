from django.conf import settings
from django.db import migrations, models
from django.utils import timezone

import subjects.models
from subjects.utils import parse_period_string


def seed_period_setting(apps, schema_editor):
    PeriodSetting = apps.get_model("subjects", "PeriodSetting")
    season, year = parse_period_string(getattr(settings, "SUBJECT_DEFAULT_PERIOD", ""))
    if not (season and year):
        now = timezone.now()
        season = "O" if now.month <= 6 else "P"
        year = now.year
    PeriodSetting.objects.update_or_create(
        pk=1,
        defaults={
            "period_season": season,
            "period_year": year,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("subjects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PeriodSetting",
            fields=[
                (
                    "id",
                    models.PositiveSmallIntegerField(
                        default=1, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "period_season",
                    models.CharField(choices=[("O", "Otoño"), ("P", "Primavera")], max_length=1),
                ),
                ("period_year", models.PositiveIntegerField()),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Periodo actual",
                "verbose_name_plural": "Periodo actual",
            },
        ),
        migrations.RunPython(seed_period_setting, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="subject",
            name="period_year",
            field=models.PositiveIntegerField(default=subjects.models._default_period_year),
        ),
        migrations.AlterField(
            model_name="subject",
            name="period_season",
            field=models.CharField(
                choices=[("O", "Otoño"), ("P", "Primavera")],
                default=subjects.models._default_period_season,
                max_length=1,
            ),
        ),
    ]
