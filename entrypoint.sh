#!/usr/bin/env bash
set -e

# Banderas (puedes controlarlas desde docker-compose)
: "${RUN_MIGRATIONS:=0}"
: "${CREATE_SUPERUSER:=0}"
: "${WAIT_FOR_MIGRATIONS:=1}"

# 0) Esperar DB lista (usando Django conexions)
python - <<'PY'
import time
from django.conf import settings
from django import setup as django_setup
django_setup()
from django.db import connections
from django.db.utils import OperationalError
for _ in range(60):
    try:
        connections['default'].cursor()
        break
    except OperationalError:
        time.sleep(2)
else:
    raise SystemExit("Database not available.")
PY

# 0.1) (worker/beat) Esperar a que exista la tabla de migraciones si corresponde
if [ "$WAIT_FOR_MIGRATIONS" = "1" ] && [ "$RUN_MIGRATIONS" = "0" ]; then
python - <<'PY'
import os, sys, time, pymysql

def req(name: str) -> str:
    v = os.getenv(name)
    if not v:
        sys.exit(f"Missing required env var: {name}")
    return v

db   = req("MYSQL_DATABASE")
host = req("MYSQL_HOST")
user = req("MYSQL_USER")
pwd  = req("MYSQL_PASSWORD")
port = int(req("MYSQL_PORT"))

for _ in range(120):
    try:
        conn = pymysql.connect(host=host, user=user, password=pwd, database=db, port=port)
        with conn.cursor() as c:
            c.execute("SELECT 1 FROM information_schema.tables WHERE table_schema=%s AND table_name='django_migrations'", (db,))
            if c.fetchone():
                break
    except Exception:
        pass
    time.sleep(2)
else:
    raise SystemExit("django_migrations table not found after waiting.")
PY
fi

# 1) Migraciones (solo si se pide)
if [ "$RUN_MIGRATIONS" = "1" ]; then
  python manage.py migrate --noinput
fi

# 2) Crear/actualizar superusuario (solo si se pide, y con Django cargado)
if [ "$CREATE_SUPERUSER" = "1" ]; then
python - <<'PY'
import os
from django import setup as django_setup
django_setup()
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()
def req(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise SystemExit(f"Missing required env var: {name}")
    return v

email    = req("DJANGO_SU_EMAIL")
password = req("DJANGO_SU_PASSWORD")

with transaction.atomic():
    u, created = User.objects.get_or_create(email=email)
    if created:
        u.is_staff = True
        u.is_superuser = True
        if hasattr(u, "role"):
            try:
                Role = getattr(type(u), "Role", None)
                u.role = Role.ADMIN if Role and hasattr(Role, "ADMIN") else "ADMIN"
            except Exception:
                pass
        u.set_password(password)
        u.save()
    else:
        changed = False
        if not u.is_staff or not u.is_superuser:
            u.is_staff = True; u.is_superuser = True; changed = True
        if hasattr(u, "role"):
            try:
                Role = getattr(type(u), "Role", None)
                target = Role.ADMIN if Role and hasattr(Role, "ADMIN") else "ADMIN"
                if getattr(u, "role", None) != target:
                    u.role = target; changed = True
            except Exception:
                pass
        # Solo DEV: forzar password al de .env
        if password:
            u.set_password(password); changed = True
        if changed: u.save()
PY
fi

# 3) Arrancar el proceso principal del contenedor
exec "$@"
