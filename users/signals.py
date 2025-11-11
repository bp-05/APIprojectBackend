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

    try:
        User = apps.get_model('users', 'User')
    except (LookupError, ImproperlyConfigured) as e:
        logger.error("Modelo User no disponible: %s", e)
        return

    users = payload.get('users') or []
    if users:
        try:
            with transaction.atomic():
                for u in users:
                    email = (u.get('email') or '').strip()
                    if not email:
                        continue
                    first_name = (u.get('nombre') or '').strip()
                    last_name = (u.get('apellido') or '').strip()
                    role_label = u.get('rol')
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
                    if obj.role != role_code:
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
