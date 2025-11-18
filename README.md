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
- Usa el endpoint de autenticación (ver sección **Endpoints**) con `{ "email": "<email>", "password": "<pass>" }` para obtener un par `access/refresh`.
- Refresca el token enviando `{ "refresh": "<token>" }` al endpoint de refresh descrito en la misma sección.
- Incluye `Authorization: Bearer <access>` en cada request autenticada.

## Endpoints

### Autenticacion
- `POST /api/token/` y `POST /api/token/refresh/` para emitir y refrescar tokens JWT.

### Usuarios
- `GET /api/users/me/`
- `POST /api/users/me/change-password/`
- `GET/POST/PUT/PATCH/DELETE /api/users/`
- `GET /api/users/teachers/`
- `GET/POST/PUT/PATCH/DELETE /api/teachers/`
- Notas: los campos `area` y `career` permiten asociar directores a unidades academicas, y el rol `DC` hereda permisos sobre asignaturas/tablas vinculadas a su area/carrera.

### Catalogos academicos
- `GET /api/areas/`, `GET /api/areas/{id}/`
- `GET /api/careers/`, `GET /api/careers/{id}/`
- `GET /api/subject-semesters/`, `GET /api/subject-semesters/{id}/`
- Soportan filtros (`?area=`), busqueda (`?search=`) y ordering (`?ordering=name` o `-name`).

### Asignaturas
- `GET/POST /api/subjects/`, `GET/PUT/PATCH/DELETE /api/subjects/{id}/`
- `GET /api/subjects/?code=<CODE>&section=<SECTION>` para filtros rapidos.
- `GET /api/subjects/by-code/<CODE>/<SECTION>/` (con `?period=` opcional) y `GET /api/subjects/code-sections/` para autocompletar.
- Permisos: `ADMIN`, `DAC` y grupo `vcm` ven todo, mientras que docentes solo manipulan sus asignaturas. El campo `teacher` acepta unicamente usuarios con rol `DOC`.
- Cada asignatura pertenece a un periodo (`period_season` + `period_year`); `PeriodSetting` define el periodo por defecto y expone `period_code`. Tambien expone campos derivados `phase_start_date`, `phase_end_date`, `process_start_date` y `process_end_date`.

### Stream SSE de Subjects
- `GET /api/subjects/stream/` entrega un flujo `text/event-stream` con eventos `created`, `updated`, `deleted` y `descriptor_processed`.
- Autenticacion por header o query `?token=`.
- Publica via Redis (`SUBJECT_STREAM_REDIS_URL` o `CELERY_BROKER_URL`). No se filtra por usuario; el frontend debe descartar eventos que no pueda listar.
- Ejemplo React:
  ```ts
  useEffect(() => {
    const src = new EventSource(`/api/subjects/stream/?token=${accessToken}`);
    src.onmessage = (evt) => {
      const payload = JSON.parse(evt.data);
      if (payload.event === "deleted") {
        removeSubject(payload.subject_id);
      } else {
        upsertSubject(payload);
      }
    };
    src.onerror = () => {
      // Opcional: mostrar alerta o reconectar manualmente.
    };
    return () => src.close();
  }, [accessToken]);
  ```
- Nginx/Gunicorn: usar `proxy_buffering off`, `proxy_read_timeout` alto y workers asincronos o threads suficientes.

### Recursos ligados a asignaturas
- `GET/POST /api/subject-units/`, `GET/PUT/PATCH/DELETE /api/subject-units/{id}/`
- `GET/POST /api/subject-competencies/`, `GET/PUT/PATCH/DELETE /api/subject-competencies/{id}/`
- `GET/POST /api/boundary-conditions/`, `GET/PUT/PATCH/DELETE /api/boundary-conditions/{id}/`
- `GET/POST /api/possible-counterparts/`, `GET/PUT/PATCH/DELETE /api/possible-counterparts/{id}/` (campo `interaction_type` es lista de codigos; `subject` es opcional).
- `GET/POST /api/alternances/`, `GET/PUT/PATCH/DELETE /api/alternances/{id}/`
- `GET/POST /api/api2-completions/`, `GET/PUT/PATCH/DELETE /api/api2-completions/{id}/`
- `GET/POST /api/api3-completions/`, `GET/PUT/PATCH/DELETE /api/api3-completions/{id}/`
- `GET/POST /api/period-phase-schedules/`, `GET/PUT/PATCH/DELETE /api/period-phase-schedules/{id}/` (ADMIN y COORD) para definir rangos globales de fases.

### Companies
- `GET/POST /api/companies/`, `GET/PUT/PATCH/DELETE /api/companies/{id}/`
- `GET/POST /api/problem-statements/`, `GET/PUT/PATCH/DELETE /api/problem-statements/{id}/`
- `GET/POST /api/counterpart-contacts/`, `GET/PUT/PATCH/DELETE /api/counterpart-contacts/{id}/` (contactos asociados a empresas)
- `GET/POST /api/engagement-scopes/`, `GET/PUT/PATCH/DELETE /api/engagement-scopes/{id}/` (unicos por empresa+code+section+periodo)
- Permisos: ADMIN/VCM/COORD/grupo `vcm` ven todo; docentes y directores quedan limitados a las empresas vinculadas a asignaturas donde son docentes o a su area/carrera.

### Formularios
- `GET/POST /api/forms/`, `GET/PUT/PATCH/DELETE /api/forms/{id}/`
- `GET/POST /api/form-templates/`, `GET/PUT/PATCH/DELETE /api/form-templates/{id}/`
- El recurso `forms` expone acciones personalizadas `submit` y `approve` (solo staff/VCM) y estados `draft|in_review|approved`.

### Descriptores
- `GET/POST /api/descriptors/`, `GET/PUT/PATCH/DELETE /api/descriptors/{id}/`
- `POST /api/descriptors/{id}/process/` para disparar el pipeline Celery.
- Permisos: `ADMIN`, `DAC`, `COORD` y grupo `vcm` ven todo; docentes solo los de sus asignaturas. Se valida que el PDF corresponda al `Subject` antes de procesar.

### Exportacion a Excel
- `POST /api/forms/<form_id>/export-xlsx/` genera el XLSX con la plantilla (`ficha-api` o `proyecto-api`). Requiere ser staff/VCM o docente dueño del form.

## Datos iniciales (`scripts/populate.json`)

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
  - Usa el endpoint de usuarios (ver sección **Usuarios** arriba) con `POST` y el siguiente cuerpo:
    - `email` (requerido)
    - `first_name`, `last_name`
    - `role` (`ADMIN`, `VCM`, `DAC`, `DC`, `DOC`, `COORD`)
    - `is_active` (bool, opcional)
    - `password` (requerido)
    - `password2` (requerido, debe coincidir)
  - Respuesta: datos del usuario sin contraseña.

- Actualizar usuario (solo ADMIN)
  - Usa `PUT/PATCH` sobre el endpoint de usuarios para editar `email`, `first_name`, `last_name`, `role`, `is_active`, `is_staff`, `is_superuser`.
  - Cambio de contraseña opcional: incluir `password` y `password2` (deben coincidir). No se devuelve la contraseña.

- Cambiar mi contraseña (usuario autenticado)
  - Usa la acción `change-password` del recurso `users/me` con `old_password`, `new_password`, `new_password2`.

## Procesamiento de Descriptores (IA)

- Subida y disparo: usa el recurso de descriptores (ver sección **Descriptores**) para crear el registro y luego invocar su acción `process` (asíncrona via Celery).
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
- PossibleCounterpart
  - Depende: `subjects.Subject` (FK opcional), `companies.Company` (FK)
  - Reglas: único por (`subject`, `company`); cuando `subject` es NULL se permiten múltiples registros
- Api3Alternance
  - Depende: `subjects.Subject` (OneToOne)
- ApiType2Completion
  - Depende: `subjects.Subject` (OneToOne)
- ApiType3Completion
  - Depende: `subjects.Subject` (OneToOne)

Companies
- Company
  - Obligatorios: `name`, `address`, `email`, `phone`, `sector`
- ProblemStatement
  - Depende: `subjects.Subject`, `companies.Company`
- CounterpartContact
  - Depende: `companies.Company`
  - Campos: `name`, `rut` (texto <= 50), `phone`, `email`, `counterpart_area`, `role`
- CompanyEngagementScope
  - Depende: `companies.Company`
  - Campos: `subject_code`, `subject_section`, `subject_period_season`, `subject_period_year` (representan la asignatura sin FK)
  - Reglas: único por (`company`, `subject_code`, `subject_section`, `subject_period_season`, `subject_period_year`)



