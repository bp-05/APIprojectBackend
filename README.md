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


- Áreas (solo lectura)
  - `GET /api/areas/` — listar áreas disponibles (sembradas por migración)
  - `GET /api/areas/{id}/` — detalle de un área

- Semestres de asignatura (solo lectura)
  - `GET /api/subject-semesters/` — listar semestres disponibles (Primero..Décimo)
  - `GET /api/subject-semesters/{id}/` — detalle

- Asignaturas (`subjects`)
  - `GET /api/subjects/` — un docente ve solo sus asignaturas; `staff`/`vcm` ven todas
  - CRUD estándar: `POST`, `GET {id}`, `PUT|PATCH|DELETE {id}` (según permisos `IsSubjectTeacherOrAdmin`)
  - Campos obligatorios: `area` (FK) y `semester` (FK). Semestres sembrados: Primero, Segundo, Tercero, Cuarto, Quinto, Sexto, Septimo, Octavo, Noveno, Decimo.
  - Áreas sembradas: Administración; Agroindustria Y Medioambiente; Automatización, Electrónica Y Robótica; Construcción; Diseño E Industria Digital; Energía; Gastronomía; Informática, Ciberseguridad Y Telecomunicaciones; Logística; Mecánica; Minería; Salud; Turismo Y Hospitalidad.
  - Ejemplo creación: `{"code":"INF-101","name":"Intro","teacher":2,"area":8,"semester":1}`

- Plantillas de Formulario (`form-templates`)
  - CRUD estándar bajo `/api/form-templates/` (solo admin — `IsAdminUser`)

- Formularios (`forms`)
  - CRUD estándar bajo `/api/forms/` (propietario/coordinador)
  - Filtros por querystring: `?subject=<code>&template=<key>`
  - Acciones:
    - `POST /api/forms/{id}/submit/` — enviar a revisión
    - `POST /api/forms/{id}/approve/` — aprobar (solo `staff` o grupo `vcm`)

- Descriptores (`descriptors`)
  - CRUD estándar bajo `/api/descriptors/` (visibilidad como en asignaturas)
  - Acción: `POST /api/descriptors/{id}/process/` — dispara tarea Celery para procesar

- Exportación a Excel
  - `POST /api/forms/{form_id}/export-xlsx/` — devuelve archivo `.xlsx` a partir de plantilla
  - La exportación usa las plantillas en `exports_app/templates/excel/*.xlsx` y el mapeo de celdas.
    - Preferencia 1: `FormTemplate.schema.xlsx_mapping` (lista de {field, cell | label, direction}).
    - Preferencia 2: archivos JSON de mapeo por plantilla: 
      - `exports_app/templates/excel/ficha_api_celdas_de_respuestas_mapeadas.json`
      - `exports_app/templates/excel/proyecto_api_celdas_de_respuestas_mapeadas.json`
    - Los valores de `cell` pueden ser rango (`C5:D5`) o celda simple (`C5`).

## Notas de Subject
- Campo `campus` (por defecto `"chillan"`).
- Nuevo campo `hours` (entero, por defecto `0`).
- Nuevo campo `api_type` (entero, valores permitidos `1`, `2`, `3`; por defecto `1`).
- Campo `units` (JSON) con 0..4 elementos. Por defecto, se crean 3 unidades con todas las claves y valores en `null` para facilitar la lectura y edición progresiva. Cada elemento incluye las claves: `number` (1..4, puede ser null), `expected_learning`, `unit_hours` (int ≥ 0 o null), `activities_description`, `evaluation_evidence`, `evidence_detail`, `counterpart_link`, `place_mode_type`, `counterpart_participant_name`. Las claves son obligatorias, pero sus valores pueden ir en `null`.
- Campo `technical_competencies` (JSON) con 1..5 elementos. Por defecto, se crean 5 competencias con `number` de 1 a 5 y `description` vacía (`""`). Cada elemento incluye: `number` (1..5, único) y `description` (texto; permite vacío o null). Se valida máximo 5 y unicidad de `number`.
- Campo `company_boundary_conditions` (JSON) con las claves: `large_company` (bool), `medium_company` (bool), `small_company` (bool), `family_enterprise` (bool), `not_relevant` (bool), `company_type_description` (texto), `company_requirements_for_level_2_3` (texto), `project_minimum_elements` (texto). Por defecto, los booleanos van en `false` (NO) y los textos vacíos (`""`).
- Expuestos en API (`subjects`) y visibles en admin.
- `teacher` es opcional (puede crearse la asignatura sin docente y asignarse después).
- Ejemplo de creación: `{"code":"INF-101","name":"Intro","campus":"chillan","hours":0,"api_type":1,"units":[{"number":1,"expected_learning":null,"unit_hours":null,"activities_description":null,"evaluation_evidence":null,"evidence_detail":null,"counterpart_link":null,"place_mode_type":null,"counterpart_participant_name":null}],"area":8,"semester":1}` (puedes incluir `"teacher":2` si corresponde).

## Empresas (companies)
- Endpoint: `GET/POST /api/companies/`, `GET/PUT/PATCH/DELETE /api/companies/{id}/`
- Campos: `name`, `address`, `management_address` (opcional), `spys_responsible_name`, `email`, `phone`, `employees_count` (int), `sector`, `api_type` (1,2,3).
- Ejemplo creación: `{"name":"Acme Ltd","address":"Main 123","management_address":"HQ 500","spys_responsible_name":"Jane Doe","email":"jane@acme.com","phone":"+56 9 1234 5678","employees_count":120,"sector":"Manufacturing","api_type":2}`.

## Requisitos de Empresa por Asignatura (`company-requirements`)
- Cada asignatura debe tener exactamente un requisito de empresa (relación 1 a 1 con `Subject`).
- Endpoint: `GET/POST /api/company-requirements/`, `GET/PUT/PATCH/DELETE /api/company-requirements/{id}/`
- Visibilidad: docentes ven solo los requisitos de sus asignaturas; `staff`/`vcm` ven todos.
- Campos: `sector`, `worked_before` (bool), `interest_collaborate` (bool), `can_develop_activities` (bool), `willing_design_project` (bool), `interaction_type` (`virtual` | `onsite_company` | `onsite_inacap`), `has_guide` (bool), `can_receive_alternance` (bool), `alternance_students_quota` (int), `subject` (OneToOne), `company` (FK a `companies.Company`).
- Ejemplo creación: `{"sector":"IT","worked_before":false,"interest_collaborate":true,"can_develop_activities":true,"willing_design_project":true,"interaction_type":"virtual","has_guide":false,"can_receive_alternance":false,"alternance_students_quota":0,"subject":1,"company":1}`.

## Alternancia API 3 (`alternances`)
- Relación 1:1 con `Subject` cuando se ejecuta un proyecto de tipo API 3 con alternancia.
- Endpoint: `GET/POST /api/alternances/`, `GET/PUT/PATCH/DELETE /api/alternances/{id}/`
- Campos: `student_role`, `students_quota` (int), `tutor_name`, `tutor_email`, `alternance_hours` (int), `subject` (OneToOne).
- Visibilidad: docentes ven solo alternancias de sus asignaturas; `staff`/`vcm` ven todas.
- Ejemplo creación: `{"student_role":"Asistente de soporte TI","students_quota":5,"tutor_name":"Carlos Pérez","tutor_email":"c.perez@empresa.cl","alternance_hours":120,"subject":1}`.

## Completar API Tipo 2 (`api2-completions`)
- Relación 1:1 con `Subject`. Campos editables de apoyo para redacción/diseño del proyecto.
- Endpoint: `GET/POST /api/api2-completions/`, `GET/PUT/PATCH/DELETE /api/api2-completions/{id}/`
- Campos: `project_goal_students`, `deliverables_at_end`, `company_expected_participation`, `other_activities`, `subject`.
- Visibilidad: docentes ven solo los registros de sus asignaturas; `staff`/`vcm` ven todos.
- Ejemplo creación: `{"project_goal_students":"...","deliverables_at_end":"...","company_expected_participation":"...","other_activities":"...","subject":1}`.

## Completar API Tipo 3 (`api3-completions`)
- Relación 1:1 con `Subject`. Campos editables de apoyo para alternancia.
- Endpoint: `GET/POST /api/api3-completions/`, `GET/PUT/PATCH/DELETE /api/api3-completions/{id}/`
- Campos: `project_goal_students`, `deliverables_at_end`, `expected_student_role`, `other_activities`, `master_guide_expected_support`, `subject`.
- Visibilidad: docentes ven solo los registros de sus asignaturas; `staff`/`vcm` ven todos.
- Ejemplo creación: `{"project_goal_students":"...","deliverables_at_end":"...","expected_student_role":"...","other_activities":"...","master_guide_expected_support":"...","subject":1}`.

## Alcance con Contraparte (`engagement-scopes`)
- Relación 1:1 con `Subject`. Se usa para detallar el alcance del trabajo con la contraparte en la ficha proyecto API.
- Endpoint: `GET/POST /api/engagement-scopes/`, `GET/PUT/PATCH/DELETE /api/engagement-scopes/{id}/`
- Campos: `benefits_from_student` (texto), `has_value_or_research_project` (bool), `time_availability_and_participation` (texto), `workplace_has_conditions_for_group` (bool), `meeting_schedule_availability` (texto), `subject`.
- Visibilidad: docentes ven solo los registros de sus asignaturas; `staff`/`vcm` ven todos.
- Ejemplo creación: `{"benefits_from_student":"...","has_value_or_research_project":true,"time_availability_and_participation":"...","workplace_has_conditions_for_group":false,"meeting_schedule_availability":"...","subject":1}`.

## Problemática con Contraparte (`problem-statements`)
- Relación por par Asignatura–Empresa (única por combinación). Se registra la problemática a abordar y contactos de contraparte.
- Endpoint: `GET/POST /api/problem-statements/`, `GET/PUT/PATCH/DELETE /api/problem-statements/{id}/`
- Campos: `problem_to_address`, `why_important`, `stakeholders`, `related_area`, `benefits_short_medium_long_term`, `problem_definition`, `counterpart_contacts` (JSON lista de objetos con claves `name`, `counterpart_area`, `role`), `subject` (FK), `company` (FK).
- Defaults: `counterpart_contacts` inicia con un elemento con textos vacíos.
- Visibilidad: docentes ven solo registros de sus asignaturas; `staff`/`vcm` ven todos.
- Ejemplo creación: `{"problem_to_address":"...","why_important":"...","stakeholders":"...","related_area":"...","benefits_short_medium_long_term":"...","problem_definition":"...","counterpart_contacts":[{"name":"","counterpart_area":"","role":""}],"subject":1,"company":1}`.

## Claves primarias
- Todos los modelos usan un `id` autoincremental. En settings está configurado `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`.

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

