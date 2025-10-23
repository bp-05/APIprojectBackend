from django.db import migrations


def add_mapping(apps, schema_editor):
    FormTemplate = apps.get_model('forms_app', 'FormTemplate')
    updates = {
        'ficha-api': [
            {"field": "asignatura_codigo", "label": "Código", "direction": "right"},
            {"field": "asignatura_nombre", "label": "Asignatura", "direction": "right"},
            {"field": "sistema_evaluacion", "label": "Sistema de evaluación", "direction": "right"},
        ],
        'proyecto-api': [
            # add fields as needed; kept empty by default
        ],
    }
    for key, mapping in updates.items():
        try:
            tpl = FormTemplate.objects.get(key=key)
        except FormTemplate.DoesNotExist:
            continue
        schema = tpl.schema or {}
        # Do not overwrite if already configured
        if not schema.get('xlsx_mapping'):
            schema['xlsx_mapping'] = mapping
            tpl.schema = schema
            tpl.save(update_fields=['schema'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("forms_app", "0002_seed_form_templates"),
    ]

    operations = [
        migrations.RunPython(add_mapping, noop),
    ]

