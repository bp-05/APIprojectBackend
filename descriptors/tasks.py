from celery import shared_task
from django.utils import timezone
from .models import DescriptorFile
from .services import extract_text_tables
from forms_app.models import FormTemplate, FormInstance

@shared_task
def process_descriptor(descriptor_id: int):
    d = DescriptorFile.objects.get(id=descriptor_id)
    text, tables, meta = extract_text_tables(d.file.path)
    d.text_cache, d.meta, d.processed_at = text, meta, timezone.now()
    d.save(update_fields=['text_cache','meta','processed_at'])

    # ---- Pre-llenado determinista mínimo (ejemplo simple) ----
    # TODO: mejora con regex por tu formato (código, horas, etc.)
    def find_value(label):
        import re
        m = re.search(rf"{label}\s*:\s*(.+)", text, flags=re.IGNORECASE)
        return m.group(1).strip() if m else None

    base_data = {
        "asignatura_codigo": find_value("Código"),
        "asignatura_nombre": find_value("Asignatura"),
        "sistema_evaluacion": find_value("Sistema de evaluación"),
        # etc…
    }

    # Crea/actualiza instancia de FICHA API
    tpl = FormTemplate.objects.get(key="ficha-api")
    form, _ = FormInstance.objects.update_or_create(
        subject=d.subject, semester=d.semester, template=tpl,
        defaults={"data": {**(base_data or {})}, "status": "draft"}
    )

    # (opcional) crea también PROYECTO API vacío si no existe
    try:
        tpl2 = FormTemplate.objects.get(key="proyecto-api")
        FormInstance.objects.get_or_create(
            subject=d.subject, semester=d.semester, template=tpl2,
            defaults={"data": {}, "status": "draft"}
        )
    except FormTemplate.DoesNotExist:
        pass

    return form.id