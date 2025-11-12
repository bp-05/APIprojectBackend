from celery import shared_task
from django.utils import timezone
import os

from .models import DescriptorFile
from .utils_descriptor_validation import _norm_code, sanitize_subject_name, extract_code_from_path_robust
from .tasks import process_descriptor


@shared_task
def process_descriptor_strict(descriptor_id: int):
    d = DescriptorFile.objects.get(id=descriptor_id)

    # Si el descriptor ya está asociado a una asignatura manual, validar código y fijar la sección
    if d.subject_id is not None:
        file_obj = getattr(d, 'file', None)
        file_path = getattr(file_obj, 'path', None)
        file_name = getattr(file_obj, 'name', None)
        code = extract_code_from_path_robust(
            file_path,
            subject_name=getattr(d.subject, 'name', None),
            file_name=file_name,
        ) if file_path else None
        expected = _norm_code(getattr(d.subject, 'code', None))
        if not code:
            d.meta = {**(d.meta or {}), 'status': 'error', 'error': 'no es posible extraer el codigo de asignatura del pdf'}
            d.processed_at = timezone.now()
            d.save(update_fields=['meta', 'processed_at'])
            return None
        if expected and code != expected:
            d.meta = {**(d.meta or {}), 'status': 'error', 'error': 'el descriptor no corresponde a la asignatura'}
            d.processed_at = timezone.now()
            d.save(update_fields=['meta', 'processed_at'])
            return None
        # Asegurar que update_or_create use la sección de la asignatura manual
        if getattr(d.subject, 'section', None) is not None:
            os.environ['DEFAULT_SUBJECT_SECTION'] = str(d.subject.section)

    # Snapshot de campos actuales para restaurar lo no extraído
    subj_snapshot = None
    if d.subject_id is not None:
        s = d.subject
        subj_snapshot = {
            'name': s.name,
            'area_id': getattr(s.area, 'id', None),
            'semester_id': getattr(s.semester, 'id', None),
            'campus': s.campus,
            'api_type': s.api_type,
            'hours': s.hours,
            'section': s.section,
        }

    # Ejecutar el procesamiento real en este mismo proceso (no encolar otro task)
    try:
        result = process_descriptor.run(descriptor_id)
    except Exception:
        # fallback por compatibilidad
        result = process_descriptor.__wrapped__(descriptor_id)  # type: ignore

    # Post-procesamiento: en asignaturas existentes, solo sobreescribir lo extraído explícitamente
    if subj_snapshot is not None:
        d.refresh_from_db()
        s = d.subject
        meta = d.meta or {}
        extract = meta.get('extract') or {}
        subj_payload = extract.get('subject') or {}
        # name
        new_name = sanitize_subject_name(subj_payload.get('name'))
        if new_name:
            s.name = new_name
        else:
            s.name = subj_snapshot['name']
        # code no se toca; ya validado
        # area, semester, campus, api_type: restaurar siempre si fueron cambiados por defaults
        try:
            if subj_snapshot['area_id'] is not None and getattr(s.area, 'id', None) != subj_snapshot['area_id']:
                from subjects.models import Area  # import local para evitar dependencia circular en carga
                s.area_id = subj_snapshot['area_id']
        except Exception:
            pass
        try:
            if subj_snapshot['semester_id'] is not None and getattr(s.semester, 'id', None) != subj_snapshot['semester_id']:
                from subjects.models import SemesterLevel
                s.semester_id = subj_snapshot['semester_id']
        except Exception:
            pass
        s.campus = subj_snapshot['campus']
        s.api_type = subj_snapshot['api_type']
        # hours: si se puede derivar desde unidades extraídas, usarlo; si no, restaurar
        units = extract.get('subject_units') or []
        sum_units = None
        try:
            vals = [int(u.get('unit_hours')) for u in units if u.get('unit_hours') is not None]
            sum_units = sum(vals) if vals else None
        except Exception:
            sum_units = None
        s.hours = int(sum_units) if sum_units is not None else subj_snapshot['hours']
        # section: mantener snapshot
        s.section = subj_snapshot['section']
        s.save()

    return result
