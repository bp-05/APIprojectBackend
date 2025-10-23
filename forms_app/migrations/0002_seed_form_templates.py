from django.db import migrations


def seed_templates(apps, schema_editor):
    FormTemplate = apps.get_model('forms_app', 'FormTemplate')
    # Minimal, permissive schemas so PATCH validations pass
    ficha_schema = {
        "type": "object",
        "properties": {
            "asignatura_codigo": {"type": "string"},
            "asignatura_nombre": {"type": "string"},
            "sistema_evaluacion": {"type": "string"},
        },
        "additionalProperties": True,
    }
    proyecto_schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": True,
    }

    FormTemplate.objects.get_or_create(
        key="ficha-api", defaults={"version": "v1", "schema": ficha_schema}
    )
    FormTemplate.objects.get_or_create(
        key="proyecto-api", defaults={"version": "v1", "schema": proyecto_schema}
    )


def unseed_templates(apps, schema_editor):
    FormTemplate = apps.get_model('forms_app', 'FormTemplate')
    FormTemplate.objects.filter(key__in=["ficha-api", "proyecto-api"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("forms_app", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_templates, unseed_templates),
    ]

