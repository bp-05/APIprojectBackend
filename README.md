# API Backend (Django + DRF + Celery)

Backend Django/DRF con MySQL y Redis (Celery) dockerizados. Incluye JWT para autenticación y endpoints para usuarios, semestres, asignaturas, formularios, descriptores y exportación a Excel.

**Servicios**
- `web`: Django en `http://localhost:8000`
- `worker`: Celery worker
- `beat`: Celery beat
- `db`: MySQL 8
- `redis`: Redis 7

## Cómo Ejecutar
- Requisitos: `Docker` y `Docker Compose`.

1) Configurar variables de entorno
- Copia el ejemplo: `cp .env.example .env`
- Edita `.env` y completa valores (especialmente `SECRET_KEY` y credenciales de DB). Puedes validar con:
  - `python scripts/check_env.py`

2) Levantar contenedores
- `docker compose up -d --build`
- Por defecto (ver `docker-compose.yml`):
  - `RUN_MIGRATIONS=1` migra la base al iniciar `web`.
  - `CREATE_SUPERUSER=1` crea/actualiza un superusuario con `DJANGO_SU_*` del `.env`.

3) Acceso rápido
- Admin: `http://localhost:8000/admin/`
- API base: `http://localhost:8000/api/`
- Autenticación JWT: ver sección siguiente.

## Autenticación (JWT)
- Obtener token: `POST /api/token/` con `{"username":"<user>","password":"<pass>"}`
- Refrescar: `POST /api/token/refresh/` con `{"refresh":"<token>"}`
- Usa el token en `Authorization: Bearer <access>` en las llamadas a `/api/...`.

Ejemplo (curl):
```
curl -s -X POST http://localhost:8000/api/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"<tu-pass>"}'
```

## Endpoints
Todos los endpoints bajo `/api/` requieren autenticación (config global `IsAuthenticated`). Donde se indica, ciertas operaciones requieren rol de admin o pertenecer al grupo `vcm`.

- Autenticación
  - `POST /api/token/` — obtener JWT
  - `POST /api/token/refresh/` — refrescar JWT

- Usuarios
  - `GET /api/users/me/` — datos del usuario autenticado
  - `GET /api/users/` — listar usuarios (solo lectura para autenticados)
  - `POST /api/users/` — crear usuario (solo `role=ADMIN`)
  - `GET /api/users/{id}/` — detalle
  - `PUT|PATCH|DELETE /api/users/{id}/` — modificar/eliminar (solo `role=ADMIN`)

- Semestres
  - `GET /api/semesters/` — listar
  - `POST /api/semesters/` — crear
  - `GET /api/semesters/{id}/`, `PUT|PATCH|DELETE /api/semesters/{id}/`

- Asignaturas (`subjects`)
  - `GET /api/subjects/` — un docente ve solo sus asignaturas; `staff`/`vcm` ven todas
  - CRUD estándar: `POST`, `GET {id}`, `PUT|PATCH|DELETE {id}` (según permisos `IsSubjectTeacherOrAdmin`)

- Plantillas de Formulario (`form-templates`)
  - CRUD estándar bajo `/api/form-templates/` (solo admin — `IsAdminUser`)

- Formularios (`forms`)
  - CRUD estándar bajo `/api/forms/` (propietario/coordinador)
  - Filtros por querystring: `?subject=<code>&semester=<code>&template=<key>`
  - Acciones:
    - `POST /api/forms/{id}/submit/` — enviar a revisión
    - `POST /api/forms/{id}/approve/` — aprobar (solo `staff` o grupo `vcm`)

- Descriptores (`descriptors`)
  - CRUD estándar bajo `/api/descriptors/` (visibilidad como en asignaturas)
  - Acción: `POST /api/descriptors/{id}/process/` — dispara tarea Celery para procesar

- Exportación a Excel
  - `POST /api/forms/{form_id}/export-xlsx/` — devuelve archivo `.xlsx` a partir de plantilla

## Variables de Entorno Principales
- Django: `DJANGO_SETTINGS_MODULE`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- Base de datos: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`
- Redis/Celery: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- Superusuario (si `CREATE_SUPERUSER=1`): `DJANGO_SU_NAME`, `DJANGO_SU_EMAIL`, `DJANGO_SU_PASSWORD`

Valida tu configuración: `python scripts/check_env.py`

## Desarrollo
- Los volúmenes de Docker persisten datos de MySQL y archivos de usuario en `media/`.
- Para reconstruir: `docker compose build --no-cache && docker compose up -d`
- Logs rápidos: `docker compose logs -f web` | `worker` | `beat`