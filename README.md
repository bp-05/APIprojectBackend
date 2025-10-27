# API Backend (Django + DRF + Celery)

Backend Django/DRF con MySQL y Redis (Celery) dockerizados. Incluye JWT para autenticación y endpoints para usuarios, semestres, asignaturas y módulos asociados, descriptores y exportación a Excel.

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

## Endpoints (resumen)
Todos los endpoints bajo `/api/` requieren autenticación (config global `IsAuthenticated`). Donde se indica, ciertas operaciones requieren rol de admin o pertenecer al grupo `vcm`.

- Autenticación
  - `POST /api/token/`, `POST /api/token/refresh/`

- Usuarios
  - `GET /api/users/me/`
  - `GET/POST/PUT/PATCH/DELETE /api/users/`

- Áreas y Semestres (solo lectura)
  - `GET /api/areas/`, `GET /api/areas/{id}/`
  - `GET /api/subject-semesters/`, `GET /api/subject-semesters/{id}/`

- Asignaturas (`subjects`)
  - `GET/POST /api/subjects/`, `GET/PUT/PATCH/DELETE /api/subjects/{id}/`
  - Filtro: `GET /api/subjects/?code=<CODE>`
  - Detalle por código: `GET /api/subjects/by-code/<CODE>/`

- Unidades de Asignatura (`subject-units`)
  - `GET/POST /api/subject-units/`, `GET/PUT/PATCH/DELETE /api/subject-units/{id}/`
  - Campos: `subject` (FK), `number` (1..4 único por asignatura), `expected_learning`, `unit_hours`, `activities_description`, `evaluation_evidence`, `evidence_detail`, `counterpart_link`, `place_mode_type`, `counterpart_participant_name`.

- Competencias Técnicas (`subject-competencies`)
  - `GET/POST /api/subject-competencies/`, `GET/PUT/PATCH/DELETE /api/subject-competencies/{id}/`
  - Campos: `subject` (FK), `number` (1..5 único por asignatura), `description`.

- Condiciones de Borde (`boundary-conditions`)
  - `GET/POST /api/boundary-conditions/`, `GET/PUT/PATCH/DELETE /api/boundary-conditions/{id}/`
  - Campos: `subject` (OneToOne), `large_company`, `medium_company`, `small_company`, `family_enterprise`, `not_relevant` (booleans tri‑estado), `company_type_description`, `company_requirements_for_level_2_3`, `project_minimum_elements`.

- Requisitos de Empresa por Asignatura (`company-requirements`)
  - `GET/POST /api/company-requirements/`, `GET/PUT/PATCH/DELETE /api/company-requirements/{id}/`

- Alternancia API 3 (`alternances`)
  - `GET/POST /api/alternances/`, `GET/PUT/PATCH/DELETE /api/alternances/{id}/`

- Completar API Tipo 2 (`api2-completions`)
  - `GET/POST /api/api2-completions/`, `GET/PUT/PATCH/DELETE /api/api2-completions/{id}/`

- Completar API Tipo 3 (`api3-completions`)
  - `GET/POST /api/api3-completions/`, `GET/PUT/PATCH/DELETE /api/api3-completions/{id}/`

- Alcance con Contraparte (`engagement-scopes`)
  - `GET/POST /api/engagement-scopes/`, `GET/PUT/PATCH/DELETE /api/engagement-scopes/{id}/`

- Problemática con Contraparte (`problem-statements`)
  - `GET/POST /api/problem-statements/`, `GET/PUT/PATCH/DELETE /api/problem-statements/{id}/`

- Formularios y Descriptores
  - `GET/POST /api/forms/`, `GET/PUT/PATCH/DELETE /api/forms/{id}/`
  - `GET/POST /api/form-templates/`, `GET/PUT/PATCH/DELETE /api/form-templates/{id}/`
  - `GET/POST /api/descriptors/`, `GET/PUT/PATCH/DELETE /api/descriptors/{id}/`

- Exportación a Excel
  - Incluida vía `exports_app.urls` bajo `/api/`.

## Notas de Subject
- Campos: `code` (único), `name`, `campus` (por defecto "chillan"), `hours` (int, por defecto 0), `api_type` (1,2,3), `teacher` (opcional), `area` (FK), `semester` (FK).
- `teacher` es opcional; `area` y `semester` son obligatorios.

## Semillas (migración inicial)
- Áreas y Semestres se crean/aseguran en `0001_initial.py`.

## Variables de Entorno Principales
- Django: `DJANGO_SETTINGS_MODULE`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- Base de datos: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`
- Redis/Celery: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- Superusuario (si `CREATE_SUPERUSER=1`): `DJANGO_SU_NAME`, `DJANGO_SU_EMAIL`, `DJANGO_SU_PASSWORD`

## Desarrollo
- Los volúmenes de Docker persisten datos de MySQL y archivos de usuario en `media/`.
- Para reconstruir: `docker compose build --no-cache && docker compose up -d`
- Logs: `docker compose logs -f web` | `worker` | `beat`

