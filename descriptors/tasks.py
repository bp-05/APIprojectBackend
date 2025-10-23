from celery import shared_task
from django.utils import timezone
from .models import DescriptorFile
from .services import extract_text_tables
from forms_app.models import FormTemplate, FormInstance
import unicodedata


@shared_task
def process_descriptor(descriptor_id: int):
    d = DescriptorFile.objects.get(id=descriptor_id)
    text, tables, meta = extract_text_tables(d.file.path)
    d.text_cache, d.meta, d.processed_at = text, meta, timezone.now()
    d.save(update_fields=['text_cache', 'meta', 'processed_at'])

    # Pre-llenado mínimo, acento-insensible
    def _norm(s: str) -> str:
        if s is None:
            return ""
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        return s.lower()

    norm_text = _norm(text)

    def find_value(label: str):
        import re
        pattern = rf"{_norm(label)}\s*:\s*(.+)"
        m = re.search(pattern, norm_text, flags=re.IGNORECASE)
        return m.group(1).strip() if m else None

    base_data = {
        "asignatura_codigo": find_value("Código") or getattr(d.subject, 'code', None),
        "asignatura_nombre": find_value("Asignatura") or getattr(d.subject, 'name', None),
        "asignatura_area": getattr(getattr(d.subject, 'area', None), 'name', None),
        "asignatura_semestre": getattr(getattr(d.subject, 'semester', None), 'name', None),
        "sistema_evaluacion": find_value("Sistema de evaluación"),
    }

    # Crea/actualiza instancia de FICHA API
    tpl = FormTemplate.objects.get(key="ficha-api")
    form, _ = FormInstance.objects.update_or_create(
        subject=d.subject, template=tpl,
        defaults={"data": {**(base_data or {})}, "status": "draft"}
    )

    # (opcional) crea PROYECTO API vacío si no existe
    try:
        tpl2 = FormTemplate.objects.get(key="proyecto-api")
        FormInstance.objects.get_or_create(
            subject=d.subject, template=tpl2,
            defaults={"data": {}, "status": "draft"}
        )
    except FormTemplate.DoesNotExist:
        pass

    return form.id
