# API Backend (Django + DRF + Celery)

Backend Django/DRF con MySQL y Redis (Celery) dockerizados. Incluye JWT para autenticación y endpoints para usuarios, áreas/semestres, asignaturas, descriptores y exportación a Excel.

**Servicios**
- `web`: Django en `http://localhost:8000`
- `worker`: Celery worker
- `beat`: Celery beat
- `db`: MySQL 8
- `redis`: Redis 7

## Cómo Ejecutar
- Requisitos: Docker y Docker Compose

1) Variables de entorno
- Copia: `cp .env.example .env`
- Edita `.env` y completa valores (por ejemplo `SECRET_KEY`, credenciales de DB). Puedes validar con `python scripts/check_env.py`.

2) Levantar contenedores
- `docker compose up -d --build`
- Por defecto (ver `docker-compose.yml`):
  - `RUN_MIGRATIONS=1` migra la base al iniciar `web`.
  - `CREATE_SUPERUSER=1` crea/actualiza un superusuario con `DJANGO_SU_*` del `.env`.
  - El servicio `worker` usa `--concurrency=${CELERY_CONCURRENCY:-1}` para controlar el paralelismo.

3) Accesos
- Admin: `http://localhost:8000/admin/`
- API base: `http://localhost:8000/api/`

## Autenticación (JWT)
- Obtener token: `POST /api/token/` con `{ "email": "<email>", "password": "<pass>" }`
- Refrescar: `POST /api/token/refresh/` con `{ "refresh": "<token>" }`
- Usar en header: `Authorization: Bearer <access>`

## Endpoints (resumen)
- Autenticación
  - `POST /api/token/`, `POST /api/token/refresh/`

- Usuarios
  - `GET /api/users/me/`
  - `POST /api/users/me/change-password/`
  - `GET/POST/PUT/PATCH/DELETE /api/users/` (admin gestiona usuarios)
  - `GET /api/users/teachers/` (ADMIN, DAC, grupo `vcm`): lista de docentes (rol `DOC`).
  - `GET/POST/PUT/PATCH/DELETE /api/teachers/` (ADMIN, DAC): gestión segura de docentes (rol `DOC`). Se fuerza `role='DOC'` y se limitan campos a `email`, `first_name`, `last_name`, `is_active` y `password`.
  - Campos `area` y `career` (FK opcionales a `subjects.Area`/`subjects.Career`) permiten asociar directores de carrera u otros roles a su unidad académica. Si no se envían, permanecen en `null`.
  - El rol `DC` puede CRUDear asignaturas y tablas relacionadas (unidades, competencias, condiciones, etc.) del área/carrera asignada: si tiene solo `area`, accede a todas las asignaturas de esa área; si tiene solo `career`, se limita a esa carrera; si tiene ambos, se usa la carrera. Sin datos, solo puede gestionar asignaturas donde es `teacher`.

- Áreas y Semestres (solo lectura)
  - `GET /api/areas/`, `GET /api/areas/{id}/`
  - `GET /api/careers/`, `GET /api/careers/{id}/` (solo lectura)
    - Filtros: `?area=<id>`
    - Búsqueda: `?search=<nombre>`
    - Orden: `?ordering=name` o `?ordering=-name` (también `area`/`area__name`)
    - Incluye `area` y `area_name` en la respuesta
  - `GET /api/subject-semesters/`, `GET /api/subject-semesters/{id}/`

- Asignaturas
  - `GET/POST /api/subjects/`, `GET/PUT/PATCH/DELETE /api/subjects/{id}/`
  - Filtros: `GET /api/subjects/?code=<CODE>&section=<SECTION>`
  - Detalle por código+sección: `GET /api/subjects/by-code/<CODE>/<SECTION>/`
  - Autocompletado code+section: `GET /api/subjects/code-sections/`
  - Permisos: `ADMIN`, `DAC` y grupo `vcm` ven todo y pueden crear/editar/borrar; docentes sólo sus propias asignaturas.
  - Regla: el campo `teacher` sólo acepta usuarios con rol `DOC`.

- Unidades de Asignatura
  - `GET/POST /api/subject-units/`, `GET/PUT/PATCH/DELETE /api/subject-units/{id}/`

- Competencias Técnicas
  - `GET/POST /api/subject-competencies/`, `GET/PUT/PATCH/DELETE /api/subject-competencies/{id}/`

- Condiciones de Borde
  - `GET/POST /api/boundary-conditions/`, `GET/PUT/PATCH/DELETE /api/boundary-conditions/{id}/`

- Requisitos de Empresa por Asignatura
  - `GET/POST /api/company-requirements/`, `GET/PUT/PATCH/DELETE /api/company-requirements/{id}/`
  - Campo `interaction_type` (multi‑select): enviar/recibir como lista de códigos.
    - Códigos válidos: `virtual`, `onsite_inacap`, `onsite_company`.
    - Ejemplo (crear): `{ "sector": "Tecnología", ..., "interaction_type": ["virtual","onsite_inacap"], "subject": 12, "company": 5 }`
    - Admin: el campo se edita con checkboxes y se puede filtrar por `interaction_types`.

- Alternancia API 3
  - `GET/POST /api/alternances/`, `GET/PUT/PATCH/DELETE /api/alternances/{id}/`

- Completar API Tipo 2
  - `GET/POST /api/api2-completions/`, `GET/PUT/PATCH/DELETE /api/api2-completions/{id}/`

- Completar API Tipo 3
  - `GET/POST /api/api3-completions/`, `GET/PUT/PATCH/DELETE /api/api3-completions/{id}/`

- Formularios y Descriptores
  - `GET/POST /api/forms/`, `GET/PUT/PATCH/DELETE /api/forms/{id}/`
  - `GET/POST /api/form-templates/`, `GET/PUT/PATCH/DELETE /api/form-templates/{id}/`
- `GET/POST /api/descriptors/`, `GET/PUT/PATCH/DELETE /api/descriptors/{id}/`
- Permisos: `ADMIN`, `DAC`, `COORD` y grupo `vcm` ven todo; docentes solo pueden ver/gestionar descriptores de sus propias asignaturas.
  - Validación al subir descriptor asociado a una asignatura:
    - Se extrae el código de asignatura desde el PDF y se compara con el de la asignatura enviada.
    - Si no se puede extraer: 400 con `"no es posible extraer el codigo de asignatura del pdf"`.
    - Si no coincide: 400 con `"el descriptor no corresponde a la asignatura"`.
- Procesar descriptor: `POST /api/descriptors/{id}/process/`
    - Si la asignatura ya existe y no tenía descriptor:
      - Solo se sobrescriben los campos que realmente se extraen del PDF.
      - `name`: se actualiza si el PDF trae nombre; si no, se conserva el actual.
      - `hours`: se actualiza si se puede derivar desde la suma de `unit_hours` extraídas; si no, se conserva.
      - `code` y `section`: no se cambian; se valida que el PDF corresponda.
      - `area`, `semester`, `campus`, `api_type`: se conservan (no se reemplazan por valores por defecto del proceso).

- Exportación a Excel
  - Incluida via `exports_app.urls` bajo `/api/`

## Datos iniciales (`scripts/populate.json`)
- Después de cada `migrate`, `users.signals.populate_after_migrate` lee `scripts/populate.json` (si existe) y hace _upsert_ de usuarios, empresas, asignaturas y problem statements.
- En la sección `users` del JSON puedes definir `role`, `password` (solo al crear), además de `area` y `career`. Estos campos ahora enlazan con `subjects.Area` y `subjects.Career`, creando los registros si aún no existen. Esto se usa para los directores de carrera del archivo de ejemplo.
- El proceso es idempotente: actualiza nombres/roles/áreas/carreras si cambian, pero no sobreescribe contraseñas existentes.
- Para reimportar manualmente basta con ejecutar `python manage.py migrate` (reaplica la señal) o abrir un shell (`python manage.py shell`) y llamar `from users import signals; signals._load_populate_json()`.

## Proveedor de IA
- Configurable por `.env` con `AI_PROVIDER`:
  - `ollama` (por defecto): usa un servidor Ollama local o remoto.
    - `OLLAMA_BASE_URL` (ej.: `http://host.docker.internal:11434`)
    - `OLLAMA_MODEL` (ej.: `llama3.2:3b-instruct-q4_K_M` o `llama3.1:8b`)
    - `OLLAMA_NUM_CTX`, `OLLAMA_NUM_PREDICT`, `OLLAMA_KEEP_ALIVE`
  - `openai`: usa la API de OpenAI.
    - `OPENAI_API_KEY`
    - `OPENAI_MODEL` (ej.: `gpt-4o-mini`)
    - `OPENAI_BASE_URL` (opcional; default `https://api.openai.com/v1`)
- Variables comunes:
  - `LLM_TEMPERATURE` (recomendado `0` para JSON estable)
  - `LLM_TIMEOUT_SECONDS`

## Gestión de Usuarios (detalle)

- Crear usuario (solo ADMIN)
  - `POST /api/users/`
  - Body:
    - `email` (requerido)
    - `first_name`, `last_name`
    - `role` (`ADMIN`, `VCM`, `DAC`, `DC`, `DOC`, `COORD`)
    - `is_active` (bool, opcional)
    - `password` (requerido)
    - `password2` (requerido, debe coincidir)
  - Respuesta: datos del usuario sin contraseña.

- Actualizar usuario (solo ADMIN)
  - `PUT/PATCH /api/users/{id}/`
  - Body (cualquier campo admin): `email`, `first_name`, `last_name`, `role`, `is_active`, `is_staff`, `is_superuser`.
  - Cambio de contraseña opcional: incluir `password` y `password2` (deben coincidir). No se devuelve la contraseña.

- Cambiar mi contraseña (usuario autenticado)
  - `POST /api/users/me/change-password/`
  - Body: `old_password`, `new_password`, `new_password2`.

## Procesamiento de Descriptores (IA)

- Subida y disparo: `POST /api/descriptors/` y luego `POST /api/descriptors/{id}/process/` (asíncrono con Celery).
- Pipeline (local, sin cloud):
  - Extracción local de texto con PyMuPDF (fitz). No se sube el PDF a ningún servicio externo.
  - Envío del texto completo al modelo local en Ollama (una sola llamada) para generar JSON con: subject (solo horas si aparecen), technical_competencies, company_boundary_condition, api_type_2_completion, api_type_3_completion, subject_units.
  - El nombre y código de asignatura (Subject.name/Subject.code) se resuelven SOLO localmente (regex + pool de nombres + nombre del archivo). Si faltan, el descriptor se omite.
  - Normalización: si el LLM usa claves alternativas (SubjectTechnicalCompetency, SubjectUnit.units), se remapea al esquema antes de validar.
  - Inferencia de área (enum): por nombre detectado • heurísticas de código • sinónimos; si no calza, usa DEFAULT_AREA_IF_UNSURE.
  - Horas de asignatura: prioridad suma de unit_hours • regex en texto • DEFAULT_SUBJECT_HOURS.
  - Enriquecimiento PDF-only de SubjectUnit: si la IA devuelve menos unidades o faltan campos, se extraen de la tabla "Sistema de Evaluación" y líneas "Horas de la Unidad", poblando evidence, activities y hours por UA. No sobrescribe valores existentes.
  - Persistencia: crea/actualiza Subject (unicidad code+section), competencias técnicas, unidades, boundary y API2/3.
  - Un descriptor por Subject. Si ya existe uno, el nuevo queda sin vínculo (meta.status=conflict_existing_descriptor).
  - Debug en admin: text_cache (texto extraído) y meta.ai con code_trace, hours_trace y units (incluye enriched_from_pdf y hours_found por UA).
  - Configuración por .env: AI_PROVIDER=ollama, OLLAMA_BASE_URL, OLLAMA_MODEL, LLM_TEMPERATURE, LLM_TIMEOUT_SECONDS, AI_SCHEMA_VERSION, DEFAULT_*, SUBJECT_CODE_UPPERCASE, SUBJECT_NAME_TITLECASE, DESCRIPTORS_DELETE_ON_SKIP.
  - Dependencias: PyMuPDF y requests.

### Concurrencia (local)
- El worker Celery usa su valor por defecto (prefork ~ núcleos de CPU).
- Si necesitas limitarlo, edita `docker-compose.yml` y agrega `--concurrency=N` al comando del worker.
- No hay throttling/backoff de API porque el modelo es local.

## Subida sin Subject
- `DescriptorFile.subject` es opcional. Puedes subir un PDF sin asociarlo a una asignatura.
- Si se extraen `subject.code` y `subject.name`, se crea/actualiza `Subject` y el descriptor se vincula automáticamente.
- Si no, queda `meta.status=skipped_missing_subject` y se conserva `text_cache` y auditoría en `meta` para depurar.

## Notas de Subject
- Campos: `code`, `section` (default "1"), `name`, `campus` (default "chillan"), `shift` ("diurna" | "vespertina", default "diurna"), `hours` (int, default 0), `api_type` (1,2,3), `teacher` (opcional), `area` (FK), `career` (FK, opcional), `semester` (FK).
  - `area` siempre presente (útil para descriptores). `career` es opcional y pertenece a un `Area`.
- Unicidad: par (`code`, `section`). El `code` por sí solo no es único.

## Semillas (migración inicial)
- Áreas y Semestres se crean/aseguran en `subjects/migrations/0001_initial.py`.

## Variables de Entorno Principales
- Django: `DJANGO_SETTINGS_MODULE`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- Base de datos: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`
- Redis/Celery: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- Superusuario (si `CREATE_SUPERUSER=1`): `DJANGO_SU_EMAIL`, `DJANGO_SU_PASSWORD`

## Desarrollo
- Volúmenes de Docker persisten datos de MySQL y archivos de usuario en `media/`.
- Reconstruir: `docker compose build --no-cache && docker compose up -d`
- Logs: `docker compose logs -f web` | `worker` | `beat`

## Modelo y dependencias (resumen)

Subjects
- Subject
  - Depende: `users.User` (teacher, opcional), `subjects.Area`, `subjects.SemesterLevel`
  - Unicidad: (`code`, `section`)
- Area
  - Obligatorio: `name`
- SemesterLevel
  - Obligatorio: `name`
- SubjectUnit
  - Depende: `subjects.Subject`
  - Reglas: `number` 1..4 único por (`subject`, `number`)
- SubjectTechnicalCompetency
  - Depende: `subjects.Subject`
  - Reglas: `number` 1..5 único por (`subject`, `number`)
- CompanyBoundaryCondition
  - Depende: `subjects.Subject` (OneToOne)
- CompanyRequirement
  - Depende: `subjects.Subject` (FK), `companies.Company` (FK)
  - Reglas: único por (`subject`, `company`)
- Api3Alternance
  - Depende: `subjects.Subject` (OneToOne)
- ApiType2Completion
  - Depende: `subjects.Subject` (OneToOne)
- ApiType3Completion
  - Depende: `subjects.Subject` (OneToOne)

Companies
- Company
  - Obligatorios: `name`, `address`, `spys_responsible_name`, `email`, `phone`, `sector`
- ProblemStatement
  - Depende: `subjects.Subject`, `companies.Company`
- CounterpartContact
  - Depende: `companies.ProblemStatement`
- CompanyEngagementScope
  - Depende: `companies.Company`
  - Reglas: único por (`company`, `subject_code`, `subject_section`)
