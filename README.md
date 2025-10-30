# API Backend (Django + DRF + Celery)

Backend Django/DRF con MySQL y Redis (Celery) dockerizados. Incluye JWT para autenticacion y endpoints para usuarios, semestres, asignaturas y modulos asociados, descriptores y exportacion a Excel.

**Servicios**
- `web`: Django en `http://localhost:8000`
- `worker`: Celery worker
- `beat`: Celery beat
- `db`: MySQL 8
- `redis`: Redis 7

## Como Ejecutar
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

3) Acceso rapido
- Admin: `http://localhost:8000/admin/`
- API base: `http://localhost:8000/api/`
- Autenticacion JWT: ver seccion siguiente.

## Autenticacion (JWT)
- Obtener token: `POST /api/token/` con `{ "email": "<email>", "password": "<pass>" }`
- Refrescar: `POST /api/token/refresh/` con `{ "refresh": "<token>" }`
- Usa el token en `Authorization: Bearer <access>` en las llamadas a `/api/...`.

## Endpoints (resumen)
Todos los endpoints bajo `/api/` requieren autenticacion (config global `IsAuthenticated`). Donde se indica, ciertas operaciones requieren rol de admin o pertenecer al grupo `vcm`.

- Autenticacion
  - `POST /api/token/`, `POST /api/token/refresh/`

- Usuarios
  - `GET /api/users/me/`
  - `POST /api/users/me/change-password/` (cambiar contraseña propia; body: `{ old_password, new_password, new_password2 }`)
  - `GET/POST/PUT/PATCH/DELETE /api/users/`

- Areas y Semestres (solo lectura)
  - `GET /api/areas/`, `GET /api/areas/{id}/`
  - `GET /api/subject-semesters/`, `GET /api/subject-semesters/{id}/`

- Asignaturas (`subjects`)
  - `GET/POST /api/subjects/`, `GET/PUT/PATCH/DELETE /api/subjects/{id}/`
  - Filtros: `GET /api/subjects/?code=<CODE>&section=<SECTION>`
  - Detalle por codigo+seccion: `GET /api/subjects/by-code/<CODE>/<SECTION>/`
  - Helper de autocompletado code+section: `GET /api/subjects/code-sections/` (lista de pares accesibles para el usuario autenticado: `[{ id, code, section, name }]`)

- Unidades de Asignatura (`subject-units`)
  - `GET/POST /api/subject-units/`, `GET/PUT/PATCH/DELETE /api/subject-units/{id}/`
  - Campos: `subject` (FK), `number` (1..4 unico por asignatura), `expected_learning`, `unit_hours`, `activities_description`, `evaluation_evidence`, `evidence_detail`, `counterpart_link`, `place_mode_type`, `counterpart_participant_name`.

- Competencias Tecnicas (`subject-competencies`)
  - `GET/POST /api/subject-competencies/`, `GET/PUT/PATCH/DELETE /api/subject-competencies/{id}/`
  - Campos: `subject` (FK), `number` (1..5 unico por asignatura), `description`.

- Condiciones de Borde (`boundary-conditions`)
  - `GET/POST /api/boundary-conditions/`, `GET/PUT/PATCH/DELETE /api/boundary-conditions/{id}/`

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

- Problematica con Contraparte (`problem-statements`)
  - `GET/POST /api/problem-statements/`, `GET/PUT/PATCH/DELETE /api/problem-statements/{id}/`
  - Notas:
    - El modelo vive en `companies` y asocia una problematica a una asignatura (`subject`) y una empresa (`company`). Unicidad por par (`subject`, `company`).
    - Los contactos de contraparte ahora son una tabla: `companies.CounterpartContact` relacionada a `ProblemStatement` (`problem_statement`), y se manejan como lista anidada `counterpart_contacts` en el serializer.

- Formularios y Descriptores
  - `GET/POST /api/forms/`, `GET/PUT/PATCH/DELETE /api/forms/{id}/`
  - `GET/POST /api/form-templates/`, `GET/PUT/PATCH/DELETE /api/form-templates/{id}/`
  - `GET/POST /api/descriptors/`, `GET/PUT/PATCH/DELETE /api/descriptors/{id}/`

- Exportacion a Excel
  - Incluida via `exports_app.urls` bajo `/api/`.

## Notas de Subject
- Campos: `code`, `section` (obligatorio, por defecto "1"), `name`, `campus` (por defecto "chillan"), `hours` (int, por defecto 0), `api_type` (1,2,3), `teacher` (opcional), `area` (FK), `semester` (FK).
- Unicidad: el par (`code`, `section`) debe ser unico. El `code` por si solo ya no es unico.

## Semillas (migracion inicial)
- Areas y Semestres se crean/aseguran en `subjects/migrations/0001_initial.py`.

## Variables de Entorno Principales
- Django: `DJANGO_SETTINGS_MODULE`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- Base de datos: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`
- Redis/Celery: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- Superusuario (si `CREATE_SUPERUSER=1`): `DJANGO_SU_EMAIL`, `DJANGO_SU_PASSWORD`

## Desarrollo
- Los volumenes de Docker persisten datos de MySQL y archivos de usuario en `media/`.
- Para reconstruir: `docker compose build --no-cache && docker compose up -d`
- Logs: `docker compose logs -f web` | `worker` | `beat`

## Modelo y dependencias (siempre actualizado)

Subjects
- Subject
  - Depende (FK/OneToOne): `users.User` (teacher, opcional), `subjects.Area`, `subjects.SemesterLevel`
  - Depende (no FK): unicidad por par (`code`, `section`)
  - Obligatorios: `code`, `section` (default "1"), `name`, `area`, `semester`
- Area
  - Depende (FK/OneToOne): ninguna
  - Depende (no FK): ninguna
  - Obligatorios: `name`
- SemesterLevel
  - Depende (FK/OneToOne): ninguna
  - Depende (no FK): ninguna
  - Obligatorios: `name`
- SubjectUnit
  - Depende (FK/OneToOne): `subjects.Subject`
  - Depende (no FK): `number` entre 1..4; unico por (`subject`, `number`)
  - Obligatorios: `subject`, `number`
- SubjectTechnicalCompetency
  - Depende (FK/OneToOne): `subjects.Subject`
  - Depende (no FK): `number` entre 1..5; unico por (`subject`, `number`)
  - Obligatorios: `subject`, `number`
- CompanyBoundaryCondition
  - Depende (FK/OneToOne): `subjects.Subject` (OneToOne)
  - Depende (no FK): ninguna
  - Obligatorios: `subject`
- CompanyRequirement
  - Depende (FK/OneToOne): `subjects.Subject` (FK), `companies.Company`
  - Depende (no FK): unicidad por par (`subject`, `company`)
  - Obligatorios: `sector`, `subject`, `company`
- Api3Alternance
  - Depende (FK/OneToOne): `subjects.Subject` (OneToOne)
  - Depende (no FK): ninguna
  - Obligatorios: `student_role`, `tutor_name`, `tutor_email`, `subject`
- ApiType2Completion
  - Depende (FK/OneToOne): `subjects.Subject` (OneToOne)
  - Depende (no FK): ninguna
  - Obligatorios: `subject`
- ApiType3Completion
  - Depende (FK/OneToOne): `subjects.Subject` (OneToOne)
  - Depende (no FK): ninguna
  - Obligatorios: `subject`
  
 

Companies
- Company
  - Depende (FK/OneToOne): ninguna
  - Depende (no FK): ninguna
  - Obligatorios: `name`, `address`, `spys_responsible_name`, `email`, `phone`, `sector`
- ProblemStatement
  - Depende (FK/OneToOne): `subjects.Subject`, `companies.Company`
  - Depende (no FK): ninguna
  - Obligatorios: `subject`, `company`
- CounterpartContact
  - Depende (FK/OneToOne): `companies.ProblemStatement`
  - Depende (no FK): ninguna
  - Obligatorios: `problem_statement`
- CompanyEngagementScope
  - Depende (FK/OneToOne): `companies.Company`
  - Depende (no FK): unicidad por par (`company`, `subject_code`, `subject_section`)
  - Obligatorios: `company`, `subject_code`, `subject_section`
