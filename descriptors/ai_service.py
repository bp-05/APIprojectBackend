import os
import json
import unicodedata
import requests
from typing import Any, Dict, List, Optional, Tuple

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None  # type: ignore


AREA_ENUM = [
    "Administracion",
    "Agroindustria Y Medioambiente",
    "Automatizacion, Electronica Y Robotica",
    "Construccion",
    "Diseno E Industria Digital",
    "Energia",
    "Gastronomia",
    "Informatica, Ciberseguridad Y Telecomunicaciones",
    "Logistica",
    "Mecanica",
    "Mineria",
    "Salud",
    "Turismo Y Hospitalidad",
]

# Nombres canÃ³nicos de asignaturas para coincidencia en texto/archivo
SUBJECT_NAME_POOL = [
    # Informatica y Telecomunicaciones
    "Proyecto Integrador TI",
    "Taller de Portafolio",
    "Taller de Titulo",
    "Desarrollo de Aplicaciones Moviles",
    "Desarrollo Backend",
    "Desarrollo Frontend",
    "Ingenieria de Software",
    "Integracion Continua y Entrega Continua",
    "Arquitectura de Software",
    "DevOps",
    "Cloud Computing",
    "Ciberseguridad Aplicada",
    "Gestion de Proyectos TI",
    "UX/UI Aplicado",
    # Construccion y Geomensura
    "Proyecto de Construccion",
    "Gestion de Obras",
    "Control de Calidad en Obras",
    "Planificacion y Control de Obras",
    "Evaluacion de Proyectos de Construccion",
    "BIM Aplicado",
    "Topografia Aplicada",
    "Energias Renovables Aplicadas",
    "Automatizacion y PLC",
    # Administracion y Negocios
    "Proyecto Integrador de Negocios",
    "Plan de Negocios",
    "Emprendimiento e Innovacion",
    "Evaluacion de Proyectos",
    "Control de Gestion Aplicado",
    "Marketing Digital Aplicado",
    "Direccion de Proyectos",
    "Gestion de Personas Aplicada",
    "Customer Experience",
    # Gastronomia, Turismo y Hoteleria
    "Proyecto Gastronomico",
    "Gestion de Restaurantes",
    "Planificacion de Produccion Gastronomica",
    "Banqueteria y Catering",
    "Gestion de Operaciones Hoteleras",
    "Gestion de Eventos",
    "Turismo Sustentable",
    # Salud
    "Taller de Integracion Profesional",
    "Educacion para la Salud",
    "Atencion Primaria de Salud",
    "Practica Profesional",
    # Diseno, Audiovisual y Sonido
    "Proyecto de Diseno",
    "Produccion Audiovisual",
    "Produccion Musical",
    "Postproduccion",
    "Diseno UX Aplicado",
]

NAME_TO_ENUM_AREA: Dict[str, str] = {
    # Informatica y Telecomunicaciones
    "Proyecto Integrador TI": "Informatica, Ciberseguridad Y Telecomunicaciones",
    "Taller de Portafolio": "Informatica, Ciberseguridad Y Telecomunicaciones",
    "Taller de Titulo": "Informatica, Ciberseguridad Y Telecomunicaciones",
    "Desarrollo de Aplicaciones Moviles": "Informatica, Ciberseguridad Y Telecomunicaciones",
    "Desarrollo Backend": "Informatica, Ciberseguridad Y Telecomunicaciones",
    "Desarrollo Frontend": "Informatica, Ciberseguridad Y Telecomunicaciones",
    "Ingenieria de Software": "Informatica, Ciberseguridad Y Telecomunicaciones",
    "Integracion Continua y Entrega Continua": "Informatica, Ciberseguridad Y Telecomunicaciones",
    "Arquitectura de Software": "Informatica, Ciberseguridad Y Telecomunicaciones",
    "DevOps": "Informatica, Ciberseguridad Y Telecomunicaciones",
    "Cloud Computing": "Informatica, Ciberseguridad Y Telecomunicaciones",
    "Ciberseguridad Aplicada": "Informatica, Ciberseguridad Y Telecomunicaciones",
    "Gestion de Proyectos TI": "Informatica, Ciberseguridad Y Telecomunicaciones",
    "UX/UI Aplicado": "Informatica, Ciberseguridad Y Telecomunicaciones",
    # Construccion y Geomensura
    "Proyecto de Construccion": "Construccion",
    "Gestion de Obras": "Construccion",
    "Control de Calidad en Obras": "Construccion",
    "Planificacion y Control de Obras": "Construccion",
    "Evaluacion de Proyectos de Construccion": "Construccion",
    "BIM Aplicado": "Construccion",
    "Topografia Aplicada": "Construccion",
    "Energias Renovables Aplicadas": "Energia",
    "Automatizacion y PLC": "Automatizacion, Electronica Y Robotica",
    # Administracion y Negocios
    "Proyecto Integrador de Negocios": "Administracion",
    "Plan de Negocios": "Administracion",
    "Emprendimiento e Innovacion": "Administracion",
    "Evaluacion de Proyectos": "Administracion",
    "Control de Gestion Aplicado": "Administracion",
    "Marketing Digital Aplicado": "Administracion",
    "Direccion de Proyectos": "Administracion",
    "Gestion de Personas Aplicada": "Administracion",
    "Customer Experience": "Administracion",
    # Gastronomia / Turismo
    "Proyecto Gastronomico": "Gastronomia",
    "Gestion de Restaurantes": "Gastronomia",
    "Planificacion de Produccion Gastronomica": "Gastronomia",
    "Banqueteria y Catering": "Gastronomia",
    "Gestion de Operaciones Hoteleras": "Turismo Y Hospitalidad",
    "Gestion de Eventos": "Turismo Y Hospitalidad",
    "Turismo Sustentable": "Turismo Y Hospitalidad",
    # Salud
    "Taller de Integracion Profesional": "Salud",
    "Educacion para la Salud": "Salud",
    "Atencion Primaria de Salud": "Salud",
    "Practica Profesional": "Salud",
    # Diseno, Audiovisual y Sonido
    "Proyecto de Diseno": "Diseno E Industria Digital",
    "Produccion Audiovisual": "Diseno E Industria Digital",
    "Produccion Musical": "Diseno E Industria Digital",
    "Postproduccion": "Diseno E Industria Digital",
    "Diseno UX Aplicado": "Diseno E Industria Digital",
}


def _norm(s: Optional[str]) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.lower().strip()


def map_area_name(raw: Optional[str], default_area: str) -> str:
    if not raw:
        return default_area
    n = _norm(raw)
    keywords = [
        ("informatica", "Informatica, Ciberseguridad Y Telecomunicaciones"),
        ("ciberseguridad", "Informatica, Ciberseguridad Y Telecomunicaciones"),
        ("telecom", "Informatica, Ciberseguridad Y Telecomunicaciones"),
        ("admin", "Administracion"),
        ("finanza", "Administracion"),
        ("contab", "Administracion"),
        ("logistica", "Logistica"),
        ("salud", "Salud"),
        ("turismo", "Turismo Y Hospitalidad"),
        ("energia", "Energia"),
        ("mecan", "Mecanica"),
        ("mineria", "Mineria"),
        ("agro", "Agroindustria Y Medioambiente"),
        ("electron", "Automatizacion, Electronica Y Robotica"),
        ("constru", "Construccion"),
        ("dise", "Diseno E Industria Digital"),
        ("gastr", "Gastronomia"),
    ]
    for kw, area in keywords:
        if kw in n:
            return area
    for area in AREA_ENUM:
        if _norm(area) in n or n in _norm(area):
            return area
    return default_area


def get_ai_env() -> Dict[str, Any]:
    env = os.environ
    return {
        "provider": env.get("AI_PROVIDER", "ollama").lower(),
        "ollama_base_url": env.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        "model": env.get("OLLAMA_MODEL", "phi3:mini"),
        "temperature": float(env.get("LLM_TEMPERATURE", "0")),
        "timeout": float(env.get("LLM_TIMEOUT_SECONDS", "60")),
        # Opciones avanzadas de Ollama (si están definidas)
        "num_ctx": (int(env.get("OLLAMA_NUM_CTX")) if env.get("OLLAMA_NUM_CTX") else None),
        "num_predict": (int(env.get("OLLAMA_NUM_PREDICT")) if env.get("OLLAMA_NUM_PREDICT") else None),
        "keep_alive": env.get("OLLAMA_KEEP_ALIVE"),
        "schema_version": env.get("AI_SCHEMA_VERSION", "v1"),
        # Defaults for Subject creation
        "default_section": env.get("DEFAULT_SUBJECT_SECTION", "1"),
        "default_campus": env.get("DEFAULT_SUBJECT_CAMPUS", "chillan"),
        "default_api_type": int(env.get("DEFAULT_SUBJECT_API_TYPE", "1")),
        "default_hours": int(env.get("DEFAULT_SUBJECT_HOURS", "0")),
        "default_semester": env.get("DEFAULT_SEMESTER_LEVEL_NAME", "Primero"),
        "default_area": env.get("DEFAULT_AREA_IF_UNSURE", AREA_ENUM[0]),
        "delete_on_skip": env.get("DESCRIPTORS_DELETE_ON_SKIP", "true"),
    }


def get_json_schema() -> Dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "subject": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "code": {"type": "string"},
                    "area": {"type": "string", "enum": AREA_ENUM},
                    "hours": {"type": "integer", "minimum": 0},
                },
                "required": [],
            },
            "technical_competencies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "number": {"type": "integer", "minimum": 1, "maximum": 5},
                        "description": {"type": "string"},
                    },
                    "required": ["number", "description"],
                },
            },
            "company_boundary_condition": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "company_type_description": {"type": "string"},
                    "company_requirements_for_level_2_3": {"type": "string"},
                    "project_minimum_elements": {"type": "string"},
                },
            },
            "api_type_2_completion": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "project_goal_students": {"type": "string"},
                    "deliverables_at_end": {"type": "string"},
                    "company_expected_participation": {"type": "string"},
                    "other_activities": {"type": "string"},
                },
            },
            "api_type_3_completion": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "project_goal_students": {"type": "string"},
                    "deliverables_at_end": {"type": "string"},
                    "expected_student_role": {"type": "string"},
                    "other_activities": {"type": "string"},
                    "master_guide_expected_support": {"type": "string"},
                },
            },
            "subject_units": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "number": {"type": "integer", "minimum": 1, "maximum": 4},
                        "expected_learning": {"type": "string"},
                        "unit_hours": {"type": "integer", "minimum": 0},
                        "activities_description": {"type": "string"},
                        "evaluation_evidence": {"type": "string"},
                    },
                    "required": ["number"],
                },
            },
            "meta": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "pages": {"type": "integer", "minimum": 0},
                    "references": {"type": "array", "items": {"type": "object"}},
                },
            },
        },
        "required": ["subject"],
    }


def _normalize_for_match(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.lower().strip()


def _tokenize_for_match(s: str) -> List[str]:
    import re
    stop = {"de", "del", "la", "el", "y", "en", "ti"}
    tokens = re.findall(r"[a-zA-ZÃ¡Ã©Ã­Ã³ÃºÃ±ÃÃ‰ÃÃ“ÃšÃ‘]{2,}", s, flags=re.IGNORECASE)
    out: List[str] = []
    for t in tokens:
        nt = _normalize_for_match(t)
        if nt in stop:
            continue
        if len(nt) < 4:
            continue
        out.append(nt)
    return out


def match_subject_name_in_text(text: Optional[str]) -> Optional[str]:
    """Busca el mejor match del pool en `text` con normalizaciÃ³n y tolerancia.

    - 1) Coincidencia por subcadena normalizada.
    - 2) Cobertura de tokens (â‰¥60%).
    - 3) Similaridad difusa (ratio â‰¥ 0.82) contra el texto completo (barato).
    Devuelve el mejor nombre si algÃºn criterio supera umbral.
    """
    if not text:
        return None
    t = _normalize_for_match(text)
    # 1) Subcadena exacta normalizada
    for name in SUBJECT_NAME_POOL:
        if _normalize_for_match(name) in t:
            return name
    # 2) Cobertura de tokens del nombre dentro del texto
    best_name = None
    best_score = 0.0
    for name in SUBJECT_NAME_POOL:
        tokens = _tokenize_for_match(name)
        if not tokens:
            continue
        hits = sum(1 for tok in tokens if tok in t)
        coverage = hits / float(len(tokens))
        if coverage > best_score:
            best_score = coverage
            best_name = name
    if best_name and best_score >= 0.6:
        return best_name
    # 3) Similaridad difusa simple con SequenceMatcher
    try:
        import difflib
        for name in SUBJECT_NAME_POOL:
            r = difflib.SequenceMatcher(None, _normalize_for_match(name), t).ratio()
            if r >= 0.82:
                return name
    except Exception:
        pass
    return None


def extract_code_from_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    import re
    m = re.search(r"\b([A-Za-z]{2,6}[0-9]{2,4})\b", text)
    if m:
        return m.group(1)
    m2 = re.search(r"\b([A-Za-z0-9][A-Za-z0-9\-]{2,})\b", text)
    return m2.group(1) if m2 else None


def extract_code_from_text_near_name(text: Optional[str], name: Optional[str], window: int = 200) -> Optional[str]:
    if not text or not name:
        return None
    t = " ".join(text.split())
    n = " ".join(str(name).split())
    i = t.lower().find(n.lower())
    if i == -1:
        return None
    segment = t[max(0, i): i + window]
    import re
    m = re.search(r"\b([A-Za-z]{2,6}[0-9]{2,4})\b", segment)
    if m:
        return m.group(1)
    m2 = re.search(r"\b([A-Za-z0-9][A-Za-z0-9\-]{2,})\b", segment)
    return m2.group(1) if m2 else None


def subject_area_for_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    return NAME_TO_ENUM_AREA.get(name)


def area_by_code(code: Optional[str]) -> Optional[str]:
    if not code:
        return None
    c = str(code).upper()
    if c.startswith("TI") or c.startswith("INF") or "TI" in c:
        return "Informatica, Ciberseguridad Y Telecomunicaciones"
    return None


def build_system_prompt() -> str:
    return (
        "Eres un extractor acadÃ©mico. Responde en espaÃ±ol formal y tÃ©cnico. "
        "Devuelve SOLO JSON vÃ¡lido que cumpla el JSON Schema dado (claves en snake_case). "
        "No expliques ni incluyas texto fuera del JSON. Si una pieza no existe en el descriptor, usa cadena vacÃ­a. "
        "El campo 'area' DEBE pertenecer al enum provisto. Genera entre 1 y 5 competencias tÃ©cnicas concisas."
    )


def build_user_prompt() -> str:
    base = (
        "TODOS LOS EJEMPLOS QUE TE DARE A CONTINUACION FUERON SACADOS DEL TEXTO DE UN DESCRIPTOR AL AZAR, DEBES BASARTE EN LA INFORMACION DEL TEXTO DEL DESCRIPTOR QUE TIENES, los ejemplo tomalos como un ''esqueleto referencial'' de respuesta\n"
        "Hasta este punto la asignatura no esta asociada a una empresa todavia, por ello todos los campos a continuacion relacionados a una ''empresa'' se piensa como ''la empresa con la que podriamos trabajar deberia ser asi''\n"
        "Extrae los campos para SUBJECT, SubjectTechnicalCompetency, CompanyBoundaryCondition, ApiType2Completion, ApiType3Completion y SubjectUnit\n"
        "Formato frecuente para nombre y código: 'Nombre (CODIGO)'. Ej.: 'Proyecto Integrado (TIHI43)\n"
        "Considera sinónimos: Código/Sigla y Asignatura/Ramo/Módulo. Estructura conforme al schema. No inventes códigos.\n\n"
        "Instrucciones detalladas por sección (los textos de ejemplo solo marcan tono y extensión):\n"
        "- SubjectTechnicalCompetency: genera entre 1 y 5 competencias técnicas (mínimo 1), cortas, inferidas del texto del descriptor, orientadas a resultados. Ejemplos:\n" 
        "1) Administra procesos financieros en coherencia con la estrategia de la organización, fundamentando su actuar, de acuerdo a normativas y legislación vigente.\n"
        "2) Administra procesos de marketing, ventas y operaciones comerciales, considerando la situación, tendencias del mercado y  las necesidades de los consumidores, trabajando de manera colaborativa para el logro de metas conjuntas\n"
        "3) Administra procesos de gestión de personas, de acuerdo a las necesidades de la organización, normativa interna, legislación vigente y las condiciones del entorno, comunicando y transfiriendo información de manera efectiva\n" 
        "4) Diseña soluciones factibles de implementar en el ámbito de la  organización, el desarrollo de nuevos negocios y proyectos de  emprendimiento, bajo un enfoque sistémico, basado en la mejora continua y haciendo uso de tecnologías\n"
        "5) Diseña un plan de acción para la solución de problemáticas  complejas en la organización, el desarrollo de nuevos negocios  y/o proyectos de emprendimiento, basado en la mejora continua y orientando su implementación\n"
        "- CompanyBoundaryCondition: completa tres campos, aca hay ejemplos de como redactar:\n" 
        "1) company_type_description: se infiere que tipo o tipos de empresa son compatibles con la asignatura, texto de ejemplo: Empresas locales del sector productivo y/o de servicios, publicas o provadas, que incluyan en su estructura organizacional las áreas de Finanzas, Administrativo -Legal, Recursos Humanos  y Marketing, entre otras,  donde los estudiantes podrán conocer y/o proponer los  respectivos procesos, protocolos y procedimientos de o para cada área, para identificar una problematica u oportunidad en la gestión del área seleccionada y/o diseñar un plan de acción que permita dar solución a la problematica u oportunidad de mejora detectada.\n"
        "2) company_requirements_for_level_2_3: (texto de ejemplo) Según el área funcional de la empresa, los estudiantes deberán tener acceso a procedimientos, protocolos, lineamientos, politicas, información financiera, información historica y equipamiento. Considerar solicitar algunos procedimientos, información historica y características de los equipos de trabajos, dispuesto en las empresas. Estos se utilizarán  para contextualizar y complementar los requerimientos asociados  a la propuesta de proyecto de asesoría que desarrollarán los estudiantes\n" 
        "3) project_minimum_elements: (texto de ejemplo) Independiente de la naturaleza de la empresa y del área en que se generen las propuestas, el foco del proyecto de asesoría es que los estudiantes deben desarrollar previamente un análisis diagnóstico, que identifique posibles problematicas u zonas de oportunidad de mejora, cuya propuesta deberá incluir innovación en la solución.  El producto final es un proyecto de asesoría que incluirá aspectos innovadores para la solución de la problematica detectada en un área de la empresa. Debido a las caracteristicas de la asignatura, no se espera que el estudiante llegue a la fase de implementación del proyecto de asesoría, sólo a la comunicación de la propuesta.\n"
        "Ahora te dejo un resumen de que significan ApiType2Completion y ApiType3Completion: El Aprendizaje Integrado al mundo Productivo y de los Servicios busca que los estudiantes enfrenten problemas reales de empresas reales y propongan soluciones aplicables, integrando sus conocimientos académicos con la práctica profesional.\n"
        "Existen tres tipos de API:\n"
        "1.	API 1: un caso estándar definido por la casa central, trabajado a nivel nacional. (no esta presente en este caso)\n"
        "2.	API 2 (ApiType2Completion): un problema real de una empresa local, donde los estudiantes deben proponer soluciones concretas.\n"
        "3.	API 3 (ApiType3Completion): práctica breve (12 a 16 horas) dentro de una empresa, donde los alumnos participan directamente en su dinámica.\n"
        "- ApiType2Completion: completa cuatro campos con 1 párrafo cada uno:\n"
        "1) project_goal_students: (objetivo del trabajo de estudiantes) ejemplo: Los estudiantes realizan un diagnóstico integral y actualizado para evaluar la estrategia de posicionamiento de la marca propia, proporcionando recomendaciones basadas en un estudio de posicionamiento de marca. Estas sugerencias buscan resolver la problemática empresarial relacionada con el posicionamiento de marca nueva  y propia, asegurando que sean factibles de implementar y alineadas con la estrategia, necesidades y recursos de la organización.\n"
        "2) deliverables_at_end: (entregables al finalizar) ejemplo: Informe ejecutivo técnico con los resultado del estudio de posicionamiento de marca, ademas del diagnostico de la industria y marco administrativo - legal para la toma de desiciones del emprendedor, junto a las conclusiones finales respecto de si el proyecto presenta factibilidad tecnica y económica, para implementacion de estrategias.\n" 
        "3) company_expected_participation: (participación esperada de la empresa) ejemplo: Entregando información relevante de los procesos y actividades de la organización con los estudiantes, para el analisis de resultados del estudio de posicionamiento. Definiendo lineamientos que los estudinates deben seguir en la propuestas. Dando respuestas a las consultas de los estudiantes de forma oportuna. Facilitando información de parte del emprendedor. Disposición a visitar fabrica.\n"
        "4) other_activities: (otras actividades) ejemplo: Visita de la contraparte en reunión ejecutiva en sede. Visita de los estudiantes al lugar donde se presenta el análisis organizacional con la contraparte. Aplicación de Focus Group de Expertos en Estrategia.\n"
        "- ApiType3Completion: completa cinco campos con 1 párrafo cada uno (se llena de manera similar a ApiType2Completion pero con el contexto dado anteriormente sobre api 3, aqui la empresa probee tutores tambien):\n" 
        "1) project_goal_students\n"
        "2) deliverables_at_end\n"
        "3) expected_student_role (rol del estudiante)\n"
        "4) other_activities\n"
        "5) master_guide_expected_support (apoyo esperado del docente guía (de la empresa), coherente).\n"
        "- SubjectUnit: crea 1..4 unidades. Cada unidad incluye:\n" 
        "1) number: enumera en orden ascendente desde 1 hasta maximo 4 (hay asignaturas con menos de 4 unidades)\n"
        "2) expected_learning: (breve, p.ej. 'Diagnostica ... considerando ...') ejemplo: Diagnóstica el destino, para evaluar el desarrollo de experiencias turísticas, de acuerdo con planes, programas regionales y comunales, considerando la Ética y Ciudadanía.\n"
        "3) unit_hours: horas totales de unidad (a veces hay horas presenciales y virtuales, se suman para obtener las totales)\n"
        "4) activities_description: (es un texto, pero puede contener numeracion dentro, tal cual el ejemplo) ejemplos:\n"
        "1. Analiza políticas de gestión regional y comunal, relacionado con el destino.\n"
        "2. Identifica la vocación turística del destino, considerando las políticas y normativas comunales.\n"
        "3. Planifica las actividades de levantamiento de información, a partir de las necesidades y características del grupo de interés.\n"
        "4. Analiza la cadena de valor en la ejecución de las experiencias del destino, en base a la vocación turística de este.\n"
        "5. Evalúa los criterios de sostenibilidad de destinos, considerando sello “S”, los ODS, entre otros.\n"
        "6. Determina herramientas tecnológicas, a partir del levantamiento de información y su pertinencia para ello.\n"	
        "5) evaluation_evidence: ejemplo: Informe de avance sobre el diagnóstico empresarial (esto sale en el texto del descriptor, de que maneras se evaluara en la asignatura)"
    )
    # Instrucciones adicionales EXACTAS para mejorar extracción desde 'Sistema de Evaluación'
    extra_eval = (
        "\n\nA continuación, instrucciones adicionales EXACTAS (no resumir) para mejorar la extracción por unidad desde la sección 'Sistema de Evaluación' del descriptor:\n"
        "buscar \"sistema de evaluacion\" (normalizando o sin case sensitive. etc), desde ahi hacia abajo en el descriptor, esta una tabla con cada unidad de la asignatura (al ser texto no veras la tabla):\n"
        "sus columnas suelen ser:\n"
        "'UA' (numero de unidad, 1..4), \n"
        "'Evidencia' (solo es texto), \n"
        "'Criterios de evaluación' (tiene numeracion tipo 1.1.1.(el primer numero es unidad 1, para unidad dos seria 2.x.x y asi, el segundo numero es practicamente inutil, y el tercero es por si hay mas de uno en esa fila de unidad, ejemplo 1.1.1, 1.1.2 (ambos serian de la unidad 1)) ),  \n"
        "Situación de Evaluación (contiene texto y al final porcentajes de evaluacion),   \n"
        "Instrumento de Evaluación (siempre suele decir \"rubrica integrada\"), \n"
        "% Parcial (indica cuanto vale la evaluacion correspondiente a esa unidad),\n"
        " % Total (siempre es 100%)\n"
        "Delimita, por cada UA (1..4), al menos: Evidencia (mapear a evaluation_evidence) y Situación de Evaluación (mapear a activities_description), y si aparecen criterios numerados (1.1.1, 2.1.1, etc.) anótalos junto a activities_description."
    )
    pool_lines = "\n".join(f"  - {name}" for name in SUBJECT_NAME_POOL)
    ref = ("\n- Nombres de asignaturas API (referenciales):\n" + pool_lines + "\n")
    return base + extra_eval + ref



class AIExtractor:
    def __init__(self) -> None:
        cfg = get_ai_env()
        self.cfg = cfg
        self.provider = cfg.get("provider", "ollama")

    def extract_pdf_text(self, file_path: str, max_chars: int = 200_000) -> str:
        if not fitz:
            return ""
        try:
            doc = fitz.open(file_path)
            chunks: List[str] = []
            total = 0
            for i in range(doc.page_count):
                try:
                    t = doc.load_page(i).get_text("text") or ""
                except Exception:
                    t = ""
                if not t:
                    continue
                if total + len(t) > max_chars:
                    t = t[: max_chars - total]
                chunks.append(t)
                total += len(t)
                if total >= max_chars:
                    break
            return "\n\n".join(chunks)
        except Exception:
            return ""

    @staticmethod
    def _safe_load_json(text: Optional[str]) -> Dict[str, Any]:
        if not text:
            return {}
        s = str(text).strip()
        if s.startswith("```"):
            lines = s.splitlines()
            if lines and lines[0].lstrip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].lstrip().startswith("```"):
                lines = lines[:-1]
            s = "\n".join(lines).strip()
        try:
            return json.loads(s)
        except Exception:
            pass
        try:
            import re
            m = re.search(r"\{.*\}", s, flags=re.DOTALL)
            if m:
                return json.loads(m.group(0))
        except Exception:
            pass
        return {}

    def _ollama_generate_json(self, sys_prompt: str, user_prompt: str, full_text: str) -> Tuple[Dict[str, Any], Optional[str]]:
        base = self.cfg["ollama_base_url"].rstrip("/")
        url = f"{base}/api/generate"
        model = self.cfg["model"]
        temperature = self.cfg["temperature"]
        timeout = self.cfg.get("timeout", 60)
        prompt = (
            sys_prompt
            + "\n\n"
            + user_prompt
            + "\n\nTexto del descriptor (completo):\n"
            + full_text
        )
        options: Dict[str, Any] = {"temperature": temperature}
        if self.cfg.get("num_ctx") is not None:
            options["num_ctx"] = int(self.cfg["num_ctx"])  # tokens de contexto (entrada+salida)
        if self.cfg.get("num_predict") is not None:
            options["num_predict"] = int(self.cfg["num_predict"])  # tokens máximo de salida
        if self.cfg.get("keep_alive"):
            options["keep_alive"] = self.cfg["keep_alive"]  # ej.: "15m", "30m", "2h"

        payload = {
            "model": model,
            "prompt": prompt,
            "format": "json",
            "options": options,
            "stream": False,
        }
        try:
            r = requests.post(url, json=payload, timeout=timeout)
            r.raise_for_status()
            body = r.json()
            raw_text = body.get("response") if isinstance(body, dict) else None
            data = self._safe_load_json(raw_text)
            return data, raw_text
        except Exception as e:
            return {}, f"error: {e}"

    def extract_from_text(self, full_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        # Orden solicitado: primero el texto, luego instrucciones, y al final la especificaciÃ³n
        sys_prompt = build_system_prompt()
        user_instr = build_user_prompt()
        combined = (
            "Texto del descriptor (completo):\n" + full_text + "\n\n" + user_instr + "\n\n"
            "Devuelve SOLO un objeto JSON vÃ¡lido con las claves esperadas."
        )
        data, raw = self._ollama_generate_json(sys_prompt, combined, "")
        return data, {"model": self.cfg["model"], "inline_text": True, "raw_text": (raw[:2000] if raw else None)}

    def extract_name_code_from_pdf(self, file_path: str) -> Optional[Tuple[str, str]]:
        """Extrae (nombre, codigo) localmente desde el PDF.

        Estrategia:
        1) Buscar lineas con patron "Nombre (CODIGO)" en las primeras paginas.
        2) Si falla, detectar nombre desde el pool en el texto y luego extraer el codigo cercano
           o globalmente.
        """
        full_text = self.extract_pdf_text(file_path, max_chars=60_000) or ""
        if not full_text:
            return None
        import re

        # 1) Intento directo: "Nombre (CODIGO)"
        #   - Nombre: cualquier texto razonable
        #   - Codigo: 2-6 letras + 2-4 digitos (permite guiones)
        direct = re.search(
            r"(?m)^\s*(?P<name>[^\n\r]{3,120}?)\s*\(\s*(?P<code>[A-Za-z]{2,6}[0-9]{2,4}|[A-Za-z0-9][A-Za-z0-9\-]{2,})\s*\)\s*$",
            full_text
        )
        if direct:
            raw_name = (direct.group("name") or "").strip()
            raw_code = (direct.group("code") or "").strip()
            if raw_name and raw_code:
                return raw_name, raw_code

        # 2) Pool + codigo cercano/global
        pool_name = match_subject_name_in_text(full_text)
        if pool_name:
            code = extract_code_from_text_near_name(full_text, pool_name) or extract_code_from_text(full_text)
            if code:
                return pool_name, code

        # 3) Ultimo recurso: cualquier codigo global y una linea antes como nombre (arriesgado)
        code = extract_code_from_text(full_text)
        if code:
            # Tomar una linea superior a la primera aparicion del codigo como nombre tentativo
            i = full_text.lower().find(code.lower())
            if i != -1:
                start = max(0, full_text.rfind("\n", 0, i - 1))
                before = full_text[start:i].strip().splitlines()
                if before:
                    guess_name = before[-1].strip().strip(':').strip()
                    if len(guess_name) >= 3:
                        return guess_name, code

        return None

    def extract_subject_minimal_from_text(self, full_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        # No se usa: el subject (name/code) se resuelve localmente en tasks
        return {}, {"model": self.cfg["model"], "inline_text": True}

    def extract_sections_from_text(
        self,
        full_text: str,
        need_cbc: bool = True,
        need_api2: bool = True,
        need_api3: bool = True,
        need_competencies: bool = True,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        parts: List[str] = []
        if need_cbc:
            parts.append(
                "- CompanyBoundaryCondition: redacta 3 parrafos breves segun contexto del descriptor. "
                "Incluye company_type_description, company_requirements_for_level_2_3, project_minimum_elements."
            )
        if need_api2:
            parts.append(
                "- ApiType2Completion: redacta 1 parrafo por campo (project_goal_students, deliverables_at_end, company_expected_participation, other_activities)."
            )
        if need_api3:
            parts.append(
                "- ApiType3Completion: redacta 1 parrafo por campo (project_goal_students, deliverables_at_end, expected_student_role, other_activities, master_guide_expected_support)."
            )
        if need_competencies:
            parts.append(
                "- SubjectTechnicalCompetency: genera entre 1 y 5 competencias tecnicas breves y claras, numeradas."
            )
        sys_prompt = build_system_prompt()
        # Especificar claves, formato y ejemplos breves para maximizar compatibilidad
        json_spec = (
            "Devuelve SOLO un objeto JSON con estas claves (snake_case exacto):\n"
            "- technical_competencies: array de objetos {number:int 1..5, description:string}\n"
            "- company_boundary_condition: objeto {company_type_description, company_requirements_for_level_2_3, project_minimum_elements}\n"
            "- api_type_2_completion: objeto {project_goal_students, deliverables_at_end, company_expected_participation, other_activities}\n"
            "- api_type_3_completion: objeto {project_goal_students, deliverables_at_end, expected_student_role, other_activities, master_guide_expected_support}\n"
            "- subject_units (opcional si no corresponde): array de objetos {number:int 1..4, expected_learning, unit_hours?, activities_description?, evaluation_evidence?}\n"
        )
        # Construir en el orden: TEXTO -> INSTRUCCIONES -> ESPECIFICACIÃ“N JSON
        user_prompt = (
            "Texto del descriptor (completo):\n" + full_text + "\n\n"
            + "Secciones a generar: \n" + "\n".join(parts) + "\n\n"
            + build_user_prompt() + "\n" + json_spec + "\n"
            + "Devuelve SOLO ese objeto JSON."
        )
        # Pasamos el texto ya incluido; no repetirlo en _ollama_generate_json
        data, raw = self._ollama_generate_json(sys_prompt, user_prompt, "")
        return data, {"model": self.cfg["model"], "inline_text": True, "raw_text": (raw[:2000] if raw else None)}
