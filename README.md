# API Backend (Django + DRF + Celery)

Backend Django/DRF con MySQL y Redis (Celery) dockerizados. Incluye JWT para autenticaciÃƒÂ³n y endpoints para usuarios, semestres, asignaturas, formularios, descriptores y exportaciÃƒÂ³n a Excel.

**Servicios**
- `web`: Django en `http://localhost:8000`
- `worker`: Celery worker
- `beat`: Celery beat
- `db`: MySQL 8
- `redis`: Redis 7

## CÃƒÂ³mo Ejecutar
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

3) Acceso rÃƒÂ¡pido
- Admin: `http://localhost:8000/admin/`
- API base: `http://localhost:8000/api/`
- AutenticaciÃƒÂ³n JWT: ver secciÃƒÂ³n siguiente.

## AutenticaciÃƒÂ³n (JWT)
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
Todos los endpoints bajo `/api/` requieren autenticaciÃƒÂ³n (config global `IsAuthenticated`). Donde se indica, ciertas operaciones requieren rol de admin o pertenecer al grupo `vcm`.

- AutenticaciÃƒÂ³n
  - `POST /api/token/` Ã¢â‚¬â€ obtener JWT
  - `POST /api/token/refresh/` Ã¢â‚¬â€ refrescar JWT

- Usuarios
  - `GET /api/users/me/` Ã¢â‚¬â€ datos del usuario autenticado
  - `GET /api/users/` Ã¢â‚¬â€ listar usuarios (solo lectura para autenticados)
  - `POST /api/users/` Ã¢â‚¬â€ crear usuario (solo `role=ADMIN`)
  - `GET /api/users/{id}/` Ã¢â‚¬â€ detalle
  - `PUT|PATCH|DELETE /api/users/{id}/` Ã¢â‚¬â€ modificar/eliminar (solo `role=ADMIN`)


- ÃƒÂreas (solo lectura)
  - `GET /api/areas/` Ã¢â‚¬â€ listar ÃƒÂ¡reas disponibles (sembradas por migraciÃƒÂ³n)
  - `GET /api/areas/{id}/` Ã¢â‚¬â€ detalle de un ÃƒÂ¡rea

- Semestres de asignatura (solo lectura)
  - `GET /api/subject-semesters/` Ã¢â‚¬â€ listar semestres disponibles (Primero..DÃƒÂ©cimo)
  - `GET /api/subject-semesters/{id}/` Ã¢â‚¬â€ detalle

- Asignaturas (`subjects`)
  - `GET /api/subjects/` Ã¢â‚¬â€ un docente ve solo sus asignaturas; `staff`/`vcm` ven todas
  - CRUD estÃƒÂ¡ndar: `POST`, `GET {id}`, `PUT|PATCH|DELETE {id}` (segÃƒÂºn permisos `IsSubjectTeacherOrAdmin`)
  - Campos obligatorios: `area` (FK) y `semester` (FK). Semestres sembrados: Primero, Segundo, Tercero, Cuarto, Quinto, Sexto, Septimo, Octavo, Noveno, Decimo.
  - Filtro por código: `GET /api/subjects/?code=INF-101`
  - Detalle por código: `GET /api/subjects/by-code/INF-101/`
  - ÃƒÂreas sembradas: AdministraciÃƒÂ³n; Agroindustria Y Medioambiente; AutomatizaciÃƒÂ³n, ElectrÃƒÂ³nica Y RobÃƒÂ³tica; ConstrucciÃƒÂ³n; DiseÃƒÂ±o E Industria Digital; EnergÃƒÂ­a; GastronomÃƒÂ­a; InformÃƒÂ¡tica, Ciberseguridad Y Telecomunicaciones; LogÃƒÂ­stica; MecÃƒÂ¡nica; MinerÃƒÂ­a; Salud; Turismo Y Hospitalidad.
  - Ejemplo creaciÃƒÂ³n: `{"code":"INF-101","name":"Intro","teacher":2,"area":8,"semester":1}`

- Plantillas de Formulario (`form-templates`)
  - CRUD estÃƒÂ¡ndar bajo `/api/form-templates/` (solo admin Ã¢â‚¬â€ `IsAdminUser`)

- Formularios (`forms`)
  - CRUD estÃƒÂ¡ndar bajo `/api/forms/` (propietario/coordinador)
  - Filtros por querystring: `?subject=<code>&template=<key>`
  - Acciones:
    - `POST /api/forms/{id}/submit/` Ã¢â‚¬â€ enviar a revisiÃƒÂ³n
    - `POST /api/forms/{id}/approve/` Ã¢â‚¬â€ aprobar (solo `staff` o grupo `vcm`)

- Descriptores (`descriptors`)
  - CRUD estÃƒÂ¡ndar bajo `/api/descriptors/` (visibilidad como en asignaturas)
  - AcciÃƒÂ³n: `POST /api/descriptors/{id}/process/` Ã¢â‚¬â€ dispara tarea Celery para procesar

- ExportaciÃƒÂ³n a Excel
  - `POST /api/forms/{form_id}/export-xlsx/` Ã¢â‚¬â€ devuelve archivo `.xlsx` a partir de plantilla
  - La exportaciÃƒÂ³n usa las plantillas en `exports_app/templates/excel/*.xlsx` y el mapeo de celdas.
    - Preferencia 1: `FormTemplate.schema.xlsx_mapping` (lista de {field, cell | label, direction}).
    - Preferencia 2: archivos JSON de mapeo por plantilla: 
      - `exports_app/templates/excel/ficha_api_celdas_de_respuestas_mapeadas.json`
      - `exports_app/templates/excel/proyecto_api_celdas_de_respuestas_mapeadas.json`
    - Los valores de `cell` pueden ser rango (`C5:D5`) o celda simple (`C5`).

## Notas de Subject
- Campo `campus` (por defecto `"chillan"`).
- Nuevo campo `hours` (entero, por defecto `0`).
- Nuevo campo `api_type` (entero, valores permitidos `1`, `2`, `3`; por defecto `1`).
- Campo `technical_competencies` (JSON) con 1..5 elementos. Por defecto, se crean 5 competencias con `number` de 1 a 5 y `description` vacÃƒÂ­a (`""`). Cada elemento incluye: `number` (1..5, ÃƒÂºnico) y `description` (texto; permite vacÃƒÂ­o o null). Se valida mÃƒÂ¡ximo 5 y unicidad de `number`.
- Campo `company_boundary_conditions` (JSON) con las claves: `large_company` (bool), `medium_company` (bool), `small_company` (bool), `family_enterprise` (bool), `not_relevant` (bool), `company_type_description` (texto), `company_requirements_for_level_2_3` (texto), `project_minimum_elements` (texto). Por defecto, los booleanos van en `false` (NO) y los textos vacÃƒÂ­os (`""`).
- Expuestos en API (`subjects`) y visibles en admin.
- `teacher` es opcional (puede crearse la asignatura sin docente y asignarse despuÃƒÂ©s).

## Empresas (companies)
- Endpoint: `GET/POST /api/companies/`, `GET/PUT/PATCH/DELETE /api/companies/{id}/`
- Campos: `name`, `address`, `management_address` (opcional), `spys_responsible_name`, `email`, `phone`, `employees_count` (int), `sector`, `api_type` (1,2,3).
- Ejemplo creaciÃƒÂ³n: `{"name":"Acme Ltd","address":"Main 123","management_address":"HQ 500","spys_responsible_name":"Jane Doe","email":"jane@acme.com","phone":"+56 9 1234 5678","employees_count":120,"sector":"Manufacturing","api_type":2}`.

## Requisitos de Empresa por Asignatura (`company-requirements`)
- Cada asignatura debe tener exactamente un requisito de empresa (relaciÃƒÂ³n 1 a 1 con `Subject`).
- Endpoint: `GET/POST /api/company-requirements/`, `GET/PUT/PATCH/DELETE /api/company-requirements/{id}/`
- Visibilidad: docentes ven solo los requisitos de sus asignaturas; `staff`/`vcm` ven todos.
- Campos: `sector`, `worked_before` (bool), `interest_collaborate` (bool), `can_develop_activities` (bool), `willing_design_project` (bool), `interaction_type` (`virtual` | `onsite_company` | `onsite_inacap`), `has_guide` (bool), `can_receive_alternance` (bool), `alternance_students_quota` (int), `subject` (OneToOne), `company` (FK a `companies.Company`).
- Ejemplo creaciÃƒÂ³n: `{"sector":"IT","worked_before":false,"interest_collaborate":true,"can_develop_activities":true,"willing_design_project":true,"interaction_type":"virtual","has_guide":false,"can_receive_alternance":false,"alternance_students_quota":0,"subject":1,"company":1}`.

## Alternancia API 3 (`alternances`)
- RelaciÃƒÂ³n 1:1 con `Subject` cuando se ejecuta un proyecto de tipo API 3 con alternancia.
- Endpoint: `GET/POST /api/alternances/`, `GET/PUT/PATCH/DELETE /api/alternances/{id}/`
- Campos: `student_role`, `students_quota` (int), `tutor_name`, `tutor_email`, `alternance_hours` (int), `subject` (OneToOne).
- Visibilidad: docentes ven solo alternancias de sus asignaturas; `staff`/`vcm` ven todas.
- Ejemplo creaciÃƒÂ³n: `{"student_role":"Asistente de soporte TI","students_quota":5,"tutor_name":"Carlos PÃƒÂ©rez","tutor_email":"c.perez@empresa.cl","alternance_hours":120,"subject":1}`.

## Completar API Tipo 2 (`api2-completions`)
- RelaciÃƒÂ³n 1:1 con `Subject`. Campos editables de apoyo para redacciÃƒÂ³n/diseÃƒÂ±o del proyecto.
- Endpoint: `GET/POST /api/api2-completions/`, `GET/PUT/PATCH/DELETE /api/api2-completions/{id}/`
- Campos: `project_goal_students`, `deliverables_at_end`, `company_expected_participation`, `other_activities`, `subject`.
- Visibilidad: docentes ven solo los registros de sus asignaturas; `staff`/`vcm` ven todos.
- Ejemplo creaciÃƒÂ³n: `{"project_goal_students":"...","deliverables_at_end":"...","company_expected_participation":"...","other_activities":"...","subject":1}`.

## Completar API Tipo 3 (`api3-completions`)
- RelaciÃƒÂ³n 1:1 con `Subject`. Campos editables de apoyo para alternancia.
- Endpoint: `GET/POST /api/api3-completions/`, `GET/PUT/PATCH/DELETE /api/api3-completions/{id}/`
- Campos: `project_goal_students`, `deliverables_at_end`, `expected_student_role`, `other_activities`, `master_guide_expected_support`, `subject`.
- Visibilidad: docentes ven solo los registros de sus asignaturas; `staff`/`vcm` ven todos.
- Ejemplo creaciÃƒÂ³n: `{"project_goal_students":"...","deliverables_at_end":"...","expected_student_role":"...","other_activities":"...","master_guide_expected_support":"...","subject":1}`.

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
- Todos los modelos usan un `id` autoincremental. En settings estÃƒÂ¡ configurado `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`.

## Variables de Entorno Principales
- Django: `DJANGO_SETTINGS_MODULE`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- Base de datos: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`
- Redis/Celery: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- Superusuario (si `CREATE_SUPERUSER=1`): `DJANGO_SU_NAME`, `DJANGO_SU_EMAIL`, `DJANGO_SU_PASSWORD`

Valida tu configuraciÃƒÂ³n: `python scripts/check_env.py`

## Desarrollo
- Los volÃƒÂºmenes de Docker persisten datos de MySQL y archivos de usuario en `media/`.
- Para reconstruir: `docker compose build --no-cache && docker compose up -d`
- Logs rÃƒÂ¡pidos: `docker compose logs -f web` | `worker` | `beat`


## Unidades de Asignatura (subject-units)
- Relación N:1 con Subject. Cada unidad tiene 
umber (1..4, único por asignatura) y los campos de detalle.
- Endpoint: GET/POST /api/subject-units/, GET/PUT/PATCH/DELETE /api/subject-units/{id}/`n- Campos: subject (FK), 
umber (1..4), expected_learning, unit_hours (=0), ctivities_description, evaluation_evidence, evidence_detail, counterpart_link, place_mode_type, counterpart_participant_name.

## Competencias Técnicas (subject-competencies)
- Relación N:1 con Subject. Cada competencia tiene 
umber (1..5, único por asignatura) y description.
- Endpoint: GET/POST /api/subject-competencies/, GET/PUT/PATCH/DELETE /api/subject-competencies/{id}/`n- Campos: subject (FK), 
umber (1..5), description.

## Condiciones de Borde (oundary-conditions)
- Relación 1:1 con Subject.
- Endpoint: GET/POST /api/boundary-conditions/, GET/PUT/PATCH/DELETE /api/boundary-conditions/{id}/`n- Campos: subject (OneToOne), large_company, medium_company, small_company, amily_enterprise, 
ot_relevant (booleanos), company_type_description, company_requirements_for_level_2_3, project_minimum_elements (textos).
