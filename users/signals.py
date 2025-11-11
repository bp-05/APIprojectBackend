import json
import logging
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.db.utils import OperationalError, ProgrammingError
from django.dispatch import receiver
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import post_migrate


logger = logging.getLogger(__name__)


def _norm_str(s: Optional[str]) -> str:
    import unicodedata as _ud
    s = (s or "").strip().lower()
    s = _ud.normalize("NFKD", s)
    s = "".join(ch for ch in s if not _ud.combining(ch))
    return s


def _role_code_for_label(label: Optional[str]) -> Optional[str]:
    if not label:
        return None
    try:
        User = apps.get_model('users', 'User')
    except (LookupError, ImproperlyConfigured):
        return None
    norm = _norm_str(str(label))
    # Build mapping from display labels -> codes (normalized)
    mapping = {_norm_str(display): code for code, display in User.Role.choices}
    # Also accept common variants and abreviations (normalized keys)
    variants = {
        _norm_str("vinculacion con el medio"): "VCM",
        _norm_str("vinculacion medio"): "VCM",
        _norm_str("vcm"): "VCM",
        _norm_str("departamento academico"): "DAC",
        _norm_str("departamento academico y docencia"): "DAC",
        _norm_str("dac"): "DAC",
        _norm_str("director de carrera"): "DC",
        _norm_str("director carrera"): "DC",
        _norm_str("dc"): "DC",
        _norm_str("docente"): "DOC",
        _norm_str("doc"): "DOC",
        _norm_str("coordinador api"): "COORD",
        _norm_str("coordinador"): "COORD",
        _norm_str("coordinadora"): "COORD",
        _norm_str("coordinador de api"): "COORD",
        _norm_str("coordinacion api"): "COORD",
        _norm_str("admin"): "ADMIN",
        _norm_str("administrador"): "ADMIN",
        _norm_str("administradora"): "ADMIN",
    }
    if norm in mapping:
        return mapping[norm]
    return variants.get(norm)


def _load_populate_json():
    base = Path(getattr(settings, 'BASE_DIR', '.'))
    path = base / 'scripts' / 'populate.json'
    if not path.exists():
        return
    try:
        with path.open('r', encoding='utf-8') as fh:
            payload = json.load(fh)
    except Exception as e:
        logger.error("No se pudo leer scripts/populate.json: %s", e)
        return

    def _coerce_int(val, default=0):
        try:
            if val is None or val == "":
                return default
            return int(val)
        except Exception:
            return default

    # --- Users ---
    try:
        User = apps.get_model('users', 'User')
    except (LookupError, ImproperlyConfigured) as e:
        logger.error("Modelo User no disponible: %s", e)
        User = None

    users = payload.get('users') or []
    if users and User is not None:
        try:
            with transaction.atomic():
                for u in users:
                    email = (u.get('email') or '').strip()
                    if not email:
                        continue
                    first_name = (u.get('nombre') or u.get('first_name') or '').strip()
                    last_name = (u.get('apellido') or u.get('last_name') or '').strip()
                    role_label = u.get('rol') or u.get('role')
                    role_code = _role_code_for_label(role_label) or User.Role.DOC
                    password = u.get('password')

                    obj, created = User.objects.get_or_create(
                        email=email,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'role': role_code,
                        },
                    )
                    updated = False
                    # Update names/role if changed
                    if obj.first_name != first_name:
                        obj.first_name = first_name
                        updated = True
                    if obj.last_name != last_name:
                        obj.last_name = last_name
                        updated = True
                    if getattr(obj, 'role', None) != role_code:
                        obj.role = role_code
                        updated = True
                    # Only set password on create to avoid overwriting local changes
                    if created and password:
                        obj.set_password(password)
                        updated = True
                    if updated:
                        obj.save()
                logger.info("Populate: usuarios procesados: %d", len(users))
        except (OperationalError, ProgrammingError) as db_err:
            # DB not ready or table missing; skip silently
            logger.warning("Populate omitido (DB no lista): %s", db_err)
        except Exception as e:
            logger.error("Error durante populate de usuarios: %s", e)

    # --- Companies ---
    companies_list = payload.get('companies') or payload.get('companys') or []
    if companies_list:
        try:
            Company = apps.get_model('companies', 'Company')
        except (LookupError, ImproperlyConfigured) as e:
            logger.error("Modelo Company no disponible: %s", e)
            Company = None
        if Company is not None:
            try:
                with transaction.atomic():
                    created_or_updated = 0
                    for c in companies_list:
                        # Admitir claves en español o inglés
                        name = (c.get('name') or c.get('nombre') or '').strip()
                        if not name:
                            continue
                        address = (c.get('address') or c.get('direccion') or '').strip()
                        management_address = (c.get('management_address') or c.get('direccion_administracion') or '').strip()
                        spys_responsible_name = (c.get('spys_responsible_name') or c.get('responsable_spys') or '').strip()
                        email = (c.get('email') or c.get('correo') or '').strip()
                        phone = (c.get('phone') or c.get('telefono') or '').strip()
                        employees_count = _coerce_int(c.get('employees_count') or c.get('cantidad_empleados') or c.get('empleados'))
                        sector = (c.get('sector') or '').strip()

                        obj, created = Company.objects.get_or_create(
                            name=name,
                            defaults={
                                'address': address,
                                'management_address': management_address,
                                'spys_responsible_name': spys_responsible_name,
                                'email': email,
                                'phone': phone,
                                'employees_count': employees_count,
                                'sector': sector,
                            },
                        )
                        updated = False
                        if obj.address != address:
                            obj.address = address
                            updated = True
                        if obj.management_address != management_address:
                            obj.management_address = management_address
                            updated = True
                        if obj.spys_responsible_name != spys_responsible_name:
                            obj.spys_responsible_name = spys_responsible_name
                            updated = True
                        if obj.email != email:
                            obj.email = email
                            updated = True
                        if obj.phone != phone:
                            obj.phone = phone
                            updated = True
                        if obj.employees_count != employees_count:
                            obj.employees_count = employees_count
                            updated = True
                        if obj.sector != sector:
                            obj.sector = sector
                            updated = True
                        if updated:
                            obj.save()
                        if created or updated:
                            created_or_updated += 1
                    logger.info("Populate: companies procesadas: %d", created_or_updated)
            except (OperationalError, ProgrammingError) as db_err:
                logger.warning("Populate companies omitido (DB no lista): %s", db_err)
            except Exception as e:
                logger.error("Error durante populate de companies: %s", e)

    # --- Subjects ---
    subjects_list = payload.get('subjects') or []
    if subjects_list:
        try:
            Subject = apps.get_model('subjects', 'Subject')
            Area = apps.get_model('subjects', 'Area')
            Career = apps.get_model('subjects', 'Career')
            SemesterLevel = apps.get_model('subjects', 'SemesterLevel')
        except (LookupError, ImproperlyConfigured) as e:
            logger.error("Modelos de subjects no disponibles: %s", e)
            Subject = Area = Career = SemesterLevel = None

        # Helpers locales para resolver FKs
        def _find_area(name: str):
            if not name:
                return None
            n = _norm_str(name)
            for a in Area.objects.all():
                if _norm_str(a.name) == n:
                    return a
            # fallback: startswith or contains
            for a in Area.objects.all():
                an = _norm_str(a.name)
                if n.startswith(an) or an.startswith(n) or n in an or an in n:
                    return a
            # create if not found
            return Area.objects.create(name=name)

        ORDINALS = {
            '1': 'Primero', '2': 'Segundo', '3': 'Tercero', '4': 'Cuarto', '5': 'Quinto',
            '6': 'Sexto', '7': 'Septimo', '8': 'Octavo', '9': 'Noveno', '10': 'Decimo',
        }

        def _find_semester(val: str):
            if val is None:
                return None
            s = str(val).strip()
            # Map numeric string to ordinal name
            if s in ORDINALS:
                target = ORDINALS[s]
                obj = SemesterLevel.objects.filter(name__iexact=target).first()
                if obj:
                    return obj
            # Try by id
            try:
                iid = int(s)
                obj = SemesterLevel.objects.filter(id=iid).first()
                if obj:
                    return obj
            except Exception:
                pass
            # Try by normalized name
            ns = _norm_str(s)
            for sem in SemesterLevel.objects.all():
                if _norm_str(sem.name) == ns:
                    return sem
            return None

        if Subject is not None:
            try:
                with transaction.atomic():
                    upserted = 0
                    for s in subjects_list:
                        code = (s.get('code') or '').strip()
                        section = str(s.get('section') or '1').strip()
                        name = (s.get('name') or '').strip()
                        if not code or not name:
                            continue
                        campus = (s.get('campus') or 'chillan').strip()
                        phase = (s.get('phase') or 'inicio').strip().lower()
                        hours = _coerce_int(s.get('hours'), 0)
                        api_type = _coerce_int(s.get('api_type'), 1)
                        teacher_email = (s.get('teacher_email') or '').strip()
                        area_name = (s.get('area') or '').strip()
                        career_name = (s.get('career') or '').strip()
                        semester_val = s.get('semester')

                        area_obj = _find_area(area_name) if area_name else None
                        sem_obj = _find_semester(semester_val)
                        if not area_obj or not sem_obj:
                            logger.warning("Subject omitido por FK faltante: code=%s section=%s area=%s semester=%s", code, section, area_name, semester_val)
                            continue

                        career_obj = None
                        if career_name:
                            career_obj = Career.objects.filter(name__iexact=career_name).first()
                            if not career_obj:
                                # crear si no existe
                                career_obj, _ = Career.objects.get_or_create(name=career_name, defaults={"area": area_obj})
                            elif getattr(career_obj, 'area_id', None) != area_obj.id:
                                # corregir area si difiere
                                career_obj.area = area_obj
                                career_obj.save(update_fields=["area"])

                        teacher_obj = None
                        if teacher_email and User is not None:
                            teacher_obj = User.objects.filter(email__iexact=teacher_email).first()
                            if not teacher_obj:
                                # crear docente básico si no existe
                                teacher_obj = User.objects.create_user(email=teacher_email, password=None, role=getattr(User.Role, 'DOC', 'DOC'))

                        obj, created = Subject.objects.get_or_create(
                            code=code,
                            section=section,
                            defaults={
                                'name': name,
                                'campus': campus,
                                'phase': phase,
                                'hours': hours,
                                'api_type': api_type,
                                'teacher': teacher_obj,
                                'area': area_obj,
                                'career': career_obj,
                                'semester': sem_obj,
                            },
                        )
                        updated = False
                        for field, value in (
                            ("name", name), ("campus", campus), ("phase", phase), ("hours", hours), ("api_type", api_type),
                        ):
                            if getattr(obj, field) != value:
                                setattr(obj, field, value)
                                updated = True
                        if (teacher_obj is not None) and (obj.teacher_id != getattr(teacher_obj, 'id', None)):
                            obj.teacher = teacher_obj
                            updated = True
                        if obj.area_id != area_obj.id:
                            obj.area = area_obj
                            updated = True
                        if (career_obj is not None) and (obj.career_id != getattr(career_obj, 'id', None)):
                            obj.career = career_obj
                            updated = True
                        if obj.semester_id != sem_obj.id:
                            obj.semester = sem_obj
                            updated = True
                        if created or updated:
                            obj.save()
                            upserted += 1
                    logger.info("Populate: subjects procesados: %d", upserted)
            except (OperationalError, ProgrammingError) as db_err:
                logger.warning("Populate subjects omitido (DB no lista): %s", db_err)
            except Exception as e:
                logger.error("Error durante populate de subjects: %s", e)

    # --- Problem Statements ---
    ps_list = payload.get('problem_statements') or []
    if ps_list:
        try:
            ProblemStatement = apps.get_model('companies', 'ProblemStatement')
            Company = apps.get_model('companies', 'Company')
            Subject = apps.get_model('subjects', 'Subject')
        except (LookupError, ImproperlyConfigured) as e:
            logger.error("Modelos de companies/subjects no disponibles para problem_statements: %s", e)
            ProblemStatement = Company = Subject = None
        if ProblemStatement is not None and Company is not None and Subject is not None:
            try:
                with transaction.atomic():
                    upserted = 0
                    for it in ps_list:
                        subj_code = (it.get('subject_code') or '').strip()
                        subj_section = str(it.get('subject_section') or '1').strip()
                        company_name = (it.get('company') or '').strip()
                        if not subj_code or not company_name:
                            continue
                        subject = Subject.objects.filter(code=subj_code, section=subj_section).first()
                        if subject is None:
                            # Si no viene section, intentar por code único
                            matches = list(Subject.objects.filter(code=subj_code)[:2])
                            if len(matches) == 1:
                                subject = matches[0]
                        if subject is None:
                            logger.warning("ProblemStatement omitido: no se encontró Subject code=%s section=%s", subj_code, subj_section)
                            continue
                        company = Company.objects.filter(name=company_name).first()
                        if company is None:
                            logger.warning("ProblemStatement omitido: no se encontró Company name=%s", company_name)
                            continue
                        defaults = {
                            'problem_to_address': (it.get('problem_to_address') or '').strip(),
                            'why_important': (it.get('why_important') or '').strip(),
                            'stakeholders': (it.get('stakeholders') or '').strip(),
                            'related_area': (it.get('related_area') or '').strip(),
                            'benefits_short_medium_long_term': (it.get('benefits_short_medium_long_term') or '').strip(),
                            'problem_definition': (it.get('problem_definition') or '').strip(),
                        }
                        obj, created = ProblemStatement.objects.get_or_create(
                            subject=subject, company=company, defaults=defaults
                        )
                        updated = False
                        for k, v in defaults.items():
                            if getattr(obj, k) != v:
                                setattr(obj, k, v)
                                updated = True
                        if updated:
                            obj.save()
                        if created or updated:
                            upserted += 1
                    logger.info("Populate: problem_statements procesados: %d", upserted)
            except (OperationalError, ProgrammingError) as db_err:
                logger.warning("Populate problem_statements omitido (DB no lista): %s", db_err)
            except Exception as e:
                logger.error("Error durante populate de problem_statements: %s", e)


@receiver(post_migrate)
def populate_after_migrate(sender, **kwargs):
    """Carga scripts/populate.json tras migraciones si el archivo existe.

    Idempotente: usa get_or_create para evitar duplicados y no sobreescribe
    contraseñas existentes.
    """
    try:
        _load_populate_json()
    except Exception as e:
        logger.error("Fallo populate post_migrate: %s", e)
