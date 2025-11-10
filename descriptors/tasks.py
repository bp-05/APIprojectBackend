# -*- coding: latin-1 -*-
import logging
from typing import Any, Dict, List, Optional
try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from jsonschema import validate as jsonschema_validate, ValidationError

from .models import DescriptorFile
from .ai_service import (
    AIExtractor,
    get_ai_env,
    get_json_schema,
    map_area_name,
    AREA_ENUM,
    SUBJECT_NAME_POOL,  # pool disponible localmente en tasks
    extract_code_from_text,
    extract_code_from_text_near_name,
    subject_area_for_name,
    area_by_code,
)

from subjects.models import (
    Subject,
    Area,
    Career,
    SemesterLevel,
    SubjectUnit,
    SubjectTechnicalCompetency,
    CompanyBoundaryCondition,
    ApiType2Completion,
    ApiType3Completion,
)


@shared_task
def process_descriptor(descriptor_id: int):
    d = DescriptorFile.objects.get(id=descriptor_id)

    env = get_ai_env()
    extractor = AIExtractor()

    # Early exits if AI is not configured
    meta_update = {
        "ai": {
            "schema_version": env.get("schema_version"),
            "model": env.get("model"),
        },
        "status": None,
        "error": None,
    }

    logger = logging.getLogger(__name__)
    # Helpers (deben definirse antes de su primera invocacion)
    def _coerce_to_text(val: Any) -> str:
        try:
            if val is None:
                return ""
            if isinstance(val, str):
                return val.strip()
            if isinstance(val, list):
                items = [(_coerce_to_text(it) or "").strip() for it in val]
                items = [x for x in items if x]
                if not items:
                    return ""
                if max((len(x) for x in items), default=0) <= 80:
                    return " / ".join(items)
                return "\n".join(items)
            if isinstance(val, dict):
                desc = val.get("description") if isinstance(val.get("description"), str) else None
                if desc:
                    return str(desc).strip()
                if "number" in val and "description" in val:
                    try:
                        n = int(val.get("number"))
                        return f"{n}. {str(val.get('description') or '').strip()}".strip()
                    except Exception:
                        pass
                parts = []
                for k, v in val.items():
                    txt = _coerce_to_text(v)
                    if txt:
                        parts.append(f"{k}: {txt}")
                return "; ".join(parts)
            return str(val).strip()
        except Exception:
            return str(val) if val is not None else ""

    def _normalize_for_match(s: str) -> str:
        import unicodedata as _ud
        s = _ud.normalize("NFKD", s)
        s = "".join(ch for ch in s if not _ud.combining(ch))
        return s.lower().strip()

    def _tokenize_for_match(s: str) -> List[str]:
        import re
        stop = {"de", "del", "la", "el", "y", "en", "ti"}
        tokens = re.findall(r"[A-Za-z]{2,}", s, flags=re.IGNORECASE)
        out: List[str] = []
        for t in tokens:
            nt = _normalize_for_match(t)
            if nt in stop:
                continue
            if len(nt) < 4:
                continue
            out.append(nt)
        return out

    def _match_subject_name_local(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        t = _normalize_for_match(text)
        # 1) Subcadena normalizada
        for name in SUBJECT_NAME_POOL:
            if _normalize_for_match(name) in t:
                return name
        # 2) Cobertura de tokens
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
        # 3) Similaridad difusa simple
        try:
            import difflib
            for name in SUBJECT_NAME_POOL:
                r = difflib.SequenceMatcher(None, _normalize_for_match(name), t).ratio()
                if r >= 0.82:
                    return name
        except Exception:
            pass
        return None

    def _find_eval_section(text: str) -> Optional[str]:
        """Devuelve un segmento del texto a partir de 'Sistema de Evaluación' (normalizado) si existe."""
        if not text:
            return None
        import unicodedata as _ud
        def _norm_all(s: str) -> str:
            s = _ud.normalize("NFKD", s)
            s = "".join(ch for ch in s if not _ud.combining(ch))
            return s.lower()
        norm = _norm_all(text)
        key = _norm_all("sistema de evaluacion")
        idx = norm.find(key)
        if idx == -1:
            return None
        # Tomar un segmento razonable hacia abajo (p.ej. 8000 chars)
        start = idx
        end = min(len(text), start + 8000)
        return text[start:end]

    def _parse_units_from_eval_table(text: Optional[str]) -> Dict[int, Dict[str, Any]]:
        """Intenta extraer por UA (1..4) Evidencia y Situación de Evaluación desde la sección 'Sistema de Evaluación'."""
        out: Dict[int, Dict[str, Any]] = {}
        if not text:
            return out
        seg = _find_eval_section(text) or ""
        if not seg:
            return out
        import re
        # Dividir por bloques UA1..UA4
        for n in range(1,5):
            pat = re.compile(rf"(?is)UA\s*{n}(.+?)(?=UA\s*{n+1}|\Z)") if n < 4 else re.compile(rf"(?is)UA\s*{n}(.+)")
            m = pat.search(seg)
            if not m:
                continue
            blk = m.group(1)
            ev = None
            sit = None
            # Evidencia: línea o párrafo posterior a la etiqueta 'Evidencia'
            me = re.search(r"(?is)Evidenc(?:ia)?\s*[:\-]?\s*(.+?)(?=\n\s*[A-ZÁÉÍÓÚa-záéíóú].{0,20}:|\n\s*UA\s*\d|\Z)", blk)
            if me:
                ev = _coerce_to_text(me.group(1)).strip()
            ms = re.search(r"(?is)Situaci[oó]n\s+de\s+Evaluaci[oó]n\s*[:\-]?\s*(.+?)(?=\n\s*[A-ZÁÉÍÓÚa-záéíóú].{0,20}:|\n\s*UA\s*\d|\Z)", blk)
            if ms:
                sit = _coerce_to_text(ms.group(1)).strip()
            # Criterios: si aparecen 1.1.1 etc., anexarlos a 'sit'
            crits = re.findall(r"(?m)^\s*\d+\.\d+\.\d+\s+.+$", blk)
            if crits:
                crit_text = "\n".join([c.strip() for c in crits])
                sit = (sit + ("\n" if sit else "") + crit_text).strip()
            if ev or sit:
                out[n] = {}
                if ev:
                    out[n]["evaluation_evidence"] = ev
                if sit:
                    out[n]["activities_description"] = sit
        return out
    def _norm_ws(s: Optional[str]) -> Optional[str]:
        if s is None:
            return None
        s = str(s).strip()
        return " ".join(s.split()) or None

    # --- PDF-only SubjectUnit enrichment helpers ---
    def _replace_ligatures(s: str) -> str:
        return (
            s.replace("?", "fi")
            .replace("?", "fl")
            .replace("?", "ffi")
            .replace("?", "ffl")
            .replace("’", "'")
            .replace("“", '"')
            .replace("”", '"')
        )

    def _normalize_pdf_text(s: Optional[str]) -> str:
        if not s:
            return ""
        import re as _re
        s = _replace_ligatures(s)
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        s = _re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", s)  # deshifenado
        s = s.replace("?", " ")
        s = _re.sub(r"[ \t]+\n", "\n", s)
        s = _re.sub(r"[ \t]{2,}", " ", s)
        return s

    def _anchor_eval_section(text: str) -> int:
        import re as _re
        for a in (r"sistema\s+de\s+evaluaci[oó]n", r"sistema\s+de\s+evaluacion"):
            m = _re.search(a, text, _re.IGNORECASE)
            if m:
                return m.start()
        return 0

    def _trim_at_first_criterion(s: str) -> str:
        import re as _re
        m = _re.search(r"\b\d{1,2}\.\d+\.\d+\b", s)
        return s[: m.start()].rstrip() if m else s

    def _extract_unit_hours_map(text: str) -> Dict[str, int]:
        import re as _re
        rx = _re.compile(r"(?mi)^\s*(\d{1,2})\s*[\.\)]?\s*[^|\n]*\|\s*Horas\s+de\s+la\s+Unidad\s*:\s*(\d+)\b")
        out: Dict[str, int] = {}
        for m in rx.finditer(text):
            out[m.group(1)] = int(m.group(2))
        return out

    def _extract_evidence_lines(text: str):
        import re as _re
        idx = _anchor_eval_section(text)
        seg = text[idx:] if idx >= 0 else text
        rx = _re.compile(r"(?m)^\s*(\d{1,2})(?!\.)\s+([A-ZÁÉÍÓÚÑ][^:\n]{2,200})\s*$")
        out: Dict[str, str] = {}
        pos: Dict[str, int] = {}
        for m in rx.finditer(seg):
            ua = m.group(1)
            line = m.group(2).strip()
            if "Horas" in line or "|" in line:
                continue
            cleaned = _trim_at_first_criterion(line)
            if ua not in out:
                out[ua] = f"{ua} {cleaned}"
                pos[ua] = idx + m.start()
        return out, pos

    _SANITIZE_PREFIXES_LOWER = tuple(
        p.lower()
        for p in (
            "Rúbrica",
            "Rubrica",
            "Escala de apreciación",
            "Escala de apreciacion",
            "PERFIL DOCENTE",
            "PREFERENCIA",
            "OBSERVACIÓN",
            "Observación",
            "Esta unidad de aprendizaje",
            "UA ESTRATEGIA",
            "ESTRATEGIA DIDÁCTICA",
            "ESTRATEGIA DIDACTICA",
        )
    )

    def _strip_inline_admin_tokens(s: str) -> str:
        import re as _re
        return _re.sub(r"\s*(?:R[úu]brica|Escala de apreciaci[oó]n)\b.*$", "", s, flags=_re.IGNORECASE)

    def _sanitize_text_block(s: str) -> str:
        import re as _re
        lines = [ln.strip() for ln in s.splitlines()]
        kept = []
        for ln in lines:
            if not ln:
                continue
            if any(ln.lower().startswith(pfx) for pfx in _SANITIZE_PREFIXES_LOWER):
                break
            kept.append(ln)
        s2 = " ".join(kept)
        s2 = _re.sub(r"\s{2,}", " ", s2).strip()
        s2 = _strip_inline_admin_tokens(s2)
        return s2

    def _extract_criteria_by_unit(text: str):
        import re as _re
        pat = _re.compile(
            r"(?ms)^\s*(?P<ua>\d{1,2})\.(?P<sec>\d+)\.(?P<sub>\d+)\s+(?P<body>.+?)"
            r"(?=^\s*\d{1,2}\.\d+\.\d+\s+|^\s*(?:Los|Las|El|La)\s+estudiante[s]?|^\s*\d+\s*[\.\)]\s+[A-ZÁÉÍÓÚÑ]|\Z)",
            flags=_re.M | _re.S,
        )
        per_ua: Dict[str, Dict[str, tuple]] = {}
        ranges: Dict[str, tuple] = {}
        for m in pat.finditer(text):
            ua = m.group("ua")
            code = f"{m.group('ua')}.{m.group('sec')}.{m.group('sub')}"
            body = _sanitize_text_block(m.group("body"))
            full = f"{code} {body}".strip()
            start, end = m.span()
            ua_map = per_ua.setdefault(ua, {})
            if code not in ua_map or len(full) > len(ua_map[code][1]):
                ua_map[code] = ((start, end), full)
            if ua not in ranges:
                ranges[ua] = (start, end)
            else:
                s0, e0 = ranges[ua]
                ranges[ua] = (min(s0, start), max(e0, end))
        out: Dict[str, List[str]] = {}
        spans: Dict[str, tuple] = {}
        for ua, cmap in per_ua.items():
            items = sorted(cmap.values(), key=lambda t: t[0][0])
            out[ua] = [line for (_rng, line) in items]
            spans[ua] = (items[0][0][0], items[-1][0][1])
        return out, spans

    def _extract_situations(text: str, spans: Dict[str, tuple], evidence_pos: Dict[str, int]) -> Dict[str, str]:
        import re as _re
        preferred_verb = {"1": "elaboran", "2": "diseñan", "3": "construyen", "4": "demuestran"}
        start_rx = _re.compile(r"(?im)^\s*(?:Los|Las|El|La)\s+estudiante[s]?\b")
        crit_rx = _re.compile(r"(?m)^\s*\d{1,2}\.\d+\.\d+\s+")
        evid_rx = _re.compile(r"(?m)^\s*\d+\s*[\.\)]\s+[A-ZÁÉÍÓÚÑ]")

        def window_for_ua(ua: str):
            starts = []
            if ua in spans:
                starts.append(spans[ua][0])
            if ua in evidence_pos:
                starts.append(evidence_pos[ua])
            if not starts:
                return None
            start = max(0, min(starts) - 400)
            next_starts = []
            try:
                nxt = str(int(ua) + 1)
                if nxt in evidence_pos:
                    next_starts.append(evidence_pos[nxt])
                for k, (s, _e) in spans.items():
                    if k.isdigit() and int(k) == int(ua) + 1:
                        next_starts.append(s)
            except Exception:
                pass
            end = min(next_starts) if next_starts else min(len(text), start + 8000)
            return (start, end)

        def collect_block(slice_text: str) -> Optional[str]:
            lines = slice_text.splitlines()
            n = len(lines)
            start_idx = None
            for i, ln in enumerate(lines):
                if start_rx.match(ln):
                    start_idx = i
                    break
            if start_idx is None:
                return None
            buf: List[str] = []
            for j in range(start_idx, n):
                ln = lines[j].strip()
                if not ln:
                    if buf:
                        break
                    else:
                        continue
                if crit_rx.match(ln) or evid_rx.match(ln):
                    break
                ln = _strip_inline_admin_tokens(ln)
                if not ln:
                    break
                buf.append(ln)
            if not buf:
                return None
            s = " ".join(buf)
            return _sanitize_text_block(s) or None

        global_blks = []
        for m in start_rx.finditer(text):
            l = max(0, m.start() - 200)
            r = min(len(text), m.end() + 2000)
            blk = collect_block(text[l:r])
            if blk:
                global_blks.append((m.start(), m.end(), blk))

        out: Dict[str, str] = {}
        for ua in sorted(set(list(spans.keys()) + list(evidence_pos.keys())), key=int):
            win = window_for_ua(ua)
            candidate = None
            if win:
                left, right = win
                blk = collect_block(text[left:right])
                if blk:
                    verb = preferred_verb.get(ua, "").lower()
                    if verb and verb not in blk.lower():
                        local_blks = []
                        slice_text = text[left:right]
                        for m in start_rx.finditer(slice_text):
                            l2 = max(0, m.start() - 50)
                            r2 = min(len(slice_text), m.end() + 2000)
                            b2 = collect_block(slice_text[l2:r2])
                            if b2:
                                local_blks.append(b2)
                        verb_blks = [b for b in local_blks if verb in b.lower()]
                        candidate = max(verb_blks, key=len) if verb_blks else blk
                    else:
                        candidate = blk
            if not candidate and global_blks and win:
                left, right = win
                center_ref = (left + right) // 2
                verb = preferred_verb.get(ua, "").lower()
                def score(item):
                    a, b, s = item
                    dist = abs(((a + b) // 2) - center_ref)
                    penalty = 0 if verb and verb in s.lower() else 1
                    return (penalty, dist, -len(s))
                candidate = min(global_blks, key=score)[2]
            if candidate and len(candidate) < 60:
                candidate = None
            if candidate:
                out[ua] = _sanitize_text_block(candidate)
        return out

    def _build_units_from_pdf(text: Optional[str]) -> Dict[str, Dict[str, Any]]:
        t = _normalize_pdf_text(text or "")
        if not t:
            return {}
        unit_hours = _extract_unit_hours_map(t)
        evidences, evidence_pos = _extract_evidence_lines(t)
        criteria_map, spans = _extract_criteria_by_unit(t)
        situations = _extract_situations(t, spans, evidence_pos)
        all_uas = set(unit_hours.keys()) | set(evidences.keys()) | set(criteria_map.keys()) | set(situations.keys())
        result: Dict[str, Dict[str, Any]] = {}
        for ua in sorted(all_uas, key=lambda x: int(x)):
            entry: Dict[str, Any] = {}
            if ua in evidences:
                entry["evaluation_evidence"] = evidences[ua]
            parts: List[str] = []
            if ua in situations and situations[ua]:
                parts.append(situations[ua])
            if ua in criteria_map and criteria_map[ua]:
                parts.extend(criteria_map[ua])
            if parts:
                entry["activities_description"] = "\n".join(parts)
            if ua in unit_hours:
                entry["unit_hours"] = unit_hours[ua]
            if entry:
                result[str(ua)] = entry
        return result

    def _norm_code(code: Optional[str]) -> Optional[str]:
        if code is None:
            return None
        c = "".join(ch for ch in str(code).strip() if ch.isalnum() or ch in {'-','_'})
        if not c:
            return None
        import os
        upper = str(os.environ.get('SUBJECT_CODE_UPPERCASE', 'true')).lower() in {'1','true','yes','on'}
        return c.upper() if upper else c.lower()

    def _maybe_titlecase(s: Optional[str]) -> Optional[str]:
        if s is None:
            return None
        import os
        enabled = str(os.environ.get('SUBJECT_NAME_TITLECASE', 'true')).lower() in {'1','true','yes','on'}
        return s.title() if enabled else s

    def _sanitize_subject_name(name: Optional[str]) -> Optional[str]:
        if name is None:
            return None
        s = str(name).strip()
        if not s:
            return None
        if '>' in s:
            parts = [p.strip() for p in s.split('>') if p.strip()]
            if parts:
                s = parts[-1]
        for pref in ("Asignaturas", "Administrador de Asignaturas y Programas de Estudio"):
            low = pref.lower()
            if s.lower().startswith(low + ' '):
                s = s[len(pref):].strip()
        return s or None

    # Sin throttle ni destilado: para modelo local priorizamos velocidad

    # Modelo local: no se requiere API key ni SDK externo

    # 0) Extraer texto del PDF localmente y cachearlo (PyMuPDF)
    def _extract_text_pymupdf(path: str, max_chars: int = 200_000) -> str:
        if not fitz:
            return ""
        try:
            doc = fitz.open(path)
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

    pdf_text = _extract_text_pymupdf(d.file.path)
    if not pdf_text:
        # fallback to any old extractor if available
        try:
            pdf_text = getattr(extractor, "extract_pdf_text")(d.file.path) or ""
        except Exception:
            pdf_text = ""
    # Cache de texto completo y texto destilado para admin
    def _distill_text_for_admin(t: Optional[str]) -> str:
        if not t:
            return ""
        # Colapsa espacios y saltos de línea, sin recortar
        return " ".join(str(t).split())

    d.text_cache = pdf_text or ""
    d.text_distilled = _distill_text_for_admin(pdf_text)
    d.save(update_fields=["text_cache", "text_distilled"])  # cache temprano para depurar

    # Intentar extraer SUBJECT (name, code) localmente antes de usar IA completa
    local_name = None
    local_code = None
    # 1.a) Por nombre de archivo: "Nombre (CODIGO).pdf" + uso temprano del pool
    try:
        if getattr(d.file, 'name', None):
            import re as _re
            base = d.file.name.replace('\\','/').rsplit('/', 1)[-1].rsplit('.', 1)[0]
            # Si el nombre del archivo contiene un nombre del pool, priorizarlo
            try:
                pool_name_fn = _match_subject_name_local(base)
            except Exception:
                pool_name_fn = None
            mfn = _re.search(r"^(?P<name>.+?)\s*\((?P<code>[A-Za-z0-9\-]{3,})\)$", base)
            if mfn:
                raw_name = (mfn.group('name') or '').strip()
                code_from_fn = (mfn.group('code') or '').strip()
                # Nombre: si el pool detecta un nombre en el filename, usarlo; si no, usar el capturado
                local_name = pool_name_fn or raw_name
                local_code = code_from_fn
            else:
                # Sin patron (Nombre (CODIGO)), intentar pool + regex de codigo dentro del filename
                if pool_name_fn:
                    near = extract_code_from_text_near_name(base, pool_name_fn) or extract_code_from_text(base)
                    if near:
                        local_name = pool_name_fn
                        local_code = near
    except Exception:
        pass
    # 1.b) Desde el texto local (primeras paginas)
    if not (local_name and local_code):
        try:
            nm, cd = extractor.extract_name_code_from_pdf(d.file.path)
            local_name = local_name or nm
            local_code = local_code or cd
        except Exception:
            pass
    # 1.c) Pool + regex en texto completo
    if not (local_name and local_code):
        try:
            pool_name = _match_subject_name_local(d.text_cache or "")
            guess_code = extract_code_from_text_near_name(d.text_cache or "", pool_name) or extract_code_from_text(d.text_cache or "")
            if pool_name and guess_code:
                local_name, local_code = pool_name, guess_code
        except Exception:
            pass

    # 1) Decidir ruta de IA: ligera (solo secciones) si ya tenemos SUBJECT local; o completa
    use_light_ai = bool(local_name and local_code)
    data = {}
    usage = None
    if use_light_ai:
        # Pre-armar subject y unidades desde el texto local
        data["subject"] = {"name": local_name, "code": local_code}
        # Persistencia temprana (antes de IA): crear/actualizar Subject y unidades locales basicas
        try:
            early_name = _sanitize_subject_name(_maybe_titlecase(_norm_ws(local_name)))
            early_code = _norm_code(local_code)
            if early_name and early_code:
                early_area_name = subject_area_for_name(early_name) or area_by_code(early_code) or env.get("default_area")
                if early_area_name not in AREA_ENUM:
                    early_area_name = env.get("default_area")
                early_semester_name = env.get("default_semester")
                # Intentar extraer unidades basicas desde el PDF
                early_units_map = {}
                try:
                    early_units_map = _build_units_from_pdf(pdf_text)
                except Exception:
                    early_units_map = {}
                with transaction.atomic():
                    area_obj, _ = Area.objects.get_or_create(name=early_area_name)
                    semester_obj, _ = SemesterLevel.objects.get_or_create(name=early_semester_name)
                    subject, _ = Subject.objects.update_or_create(
                        code=early_code,
                        section=str(env.get("default_section")),
                        defaults={
                            "name": early_name,
                            "area": area_obj,
                            "semester": semester_obj,
                            "campus": env.get("default_campus"),
                            "api_type": int(env.get("default_api_type")),
                            "hours": int(env.get("default_hours")),
                        },
                    )
                    if d.subject_id is None:
                        existing = DescriptorFile.objects.filter(subject=subject).exclude(id=d.id).first()
                        if existing is not None:
                            meta_conflict = {**(d.meta or {}), "status": "conflict_existing_descriptor", "subject_id": subject.id}
                            d.meta = meta_conflict
                            d.processed_at = timezone.now()
                            d.save(update_fields=["meta", "processed_at"])
                            logger.info("Descriptor %s not linked early: subject %s already has a descriptor (kept current record)", d.id, subject.id)
                            return None
                        d.subject = subject
                        d.save(update_fields=["subject"])
                    # Guardar unidades locales si se encuentran
                    try:
                        for ua_str, fields in (early_units_map or {}).items():
                            try:
                                num = int(ua_str)
                            except Exception:
                                continue
                            if not (1 <= num <= 4):
                                continue
                            unit, _ = SubjectUnit.objects.get_or_create(subject=subject, number=num)
                            changed = False
                            if fields.get("activities_description") and not (unit.activities_description and unit.activities_description.strip()):
                                unit.activities_description = _norm_ws(fields.get("activities_description")) or unit.activities_description
                                changed = True
                            if fields.get("evaluation_evidence") and not (unit.evaluation_evidence and unit.evaluation_evidence.strip()):
                                unit.evaluation_evidence = _norm_ws(fields.get("evaluation_evidence")) or unit.evaluation_evidence
                                changed = True
                            if fields.get("unit_hours") is not None and unit.unit_hours is None:
                                try:
                                    unit.unit_hours = int(fields.get("unit_hours") or 0)
                                    changed = True
                                except Exception:
                                    pass
                            if changed:
                                unit.save()
                    except Exception:
                                    pass
                    # Marcar meta de persistencia parcial
                    d.meta = {**(d.meta or {}), "partial_persisted": True}
                    d.save(update_fields=["meta"])
        except Exception as e:
            logger.error("Persistencia temprana fallida para descriptor %s: %s", d.id, e)

        # Unidades se parsean mÃ¡s abajo con el parser local si no vienen de IA
        # Pedir a la IA local SOLO CBC/API2/API3/competencias tecnicas
        sections, usage = extractor.extract_sections_from_text(
            pdf_text or "",
            need_cbc=True,
            need_api2=True,
            need_api3=True,
            need_competencies=True,
        )
        # Reintento programado si hay rate limit preventivo o por 429
        if isinstance(usage, dict) and usage.get("rate_limited"):
            retry_in = int(usage.get("retry_in") or 60)
            logger.warning(
                "Descriptor %s rate-limited (%s). Reintentando en %ss.",
                d.id,
                usage.get("reason") or "unknown",
                retry_in,
            )
            try:
                # Reprograma la misma tarea y termina sin tocar el descriptor
                process_descriptor.apply_async(args=[descriptor_id], countdown=retry_in)
            except Exception as e:
                logger.error("No se pudo reprogramar descriptor %s: %s", d.id, e)
            return None
        # Log de uso de tokens por llamada (visible en consola de Docker del worker)
        if isinstance(usage, dict):
            logger.info(
                "AI usage tokens: prompt=%s completion=%s total=%s model=%s provider=%s",
                usage.get("prompt_tokens"),
                usage.get("completion_tokens"),
                usage.get("total_tokens"),
                usage.get("model"),
                usage.get("provider"),
            )
        if isinstance(sections, dict):
            if isinstance(sections.get("company_boundary_condition"), dict):
                data["company_boundary_condition"] = sections["company_boundary_condition"]
            if isinstance(sections.get("api_type_2_completion"), dict):
                data["api_type_2_completion"] = sections["api_type_2_completion"]
            if isinstance(sections.get("api_type_3_completion"), dict):
                data["api_type_3_completion"] = sections["api_type_3_completion"]
            if isinstance(sections.get("technical_competencies"), list):
                data["technical_competencies"] = sections["technical_competencies"]
        meta_update.setdefault("ai", {}).update({"path": "light_sections"})
    else:
        # No pedir name/code a la IA: si no se pudo resolver localmente, omitir descriptor
        meta_update["status"] = "skipped_missing_subject"
        # Etiqueta de ruta para auditorÃ­a
        meta_update.setdefault("ai", {})["path"] = "skip_local_missing_subject"
        d.meta = {**(d.meta or {}), **meta_update, "extract": {}, "extract_minimal": {}, "text_chars": len(pdf_text or "")}
        d.processed_at = timezone.now()
        d.save(update_fields=["meta", "processed_at"])
        logger.warning("Descriptor %s skipped: missing subject name/code (local only); file=%s", d.id, getattr(d.file, 'name', ''))
        # Optional deletion
        delete_on_skip = str(env.get("delete_on_skip", "true")).lower() in {"1","true","yes","on"}
        if delete_on_skip:
            try:
                if d.file:
                    d.file.delete(save=False)
                did = d.id
                d.delete()
                logger.info("Descriptor %s deleted after skip.", did)
            except Exception as e:
                logger.error("Failed to delete skipped descriptor %s: %s", d.id, e)
        return None

    # Helper: normaliza payloads alternativos devueltos por la IA al schema esperado
    def _normalize_ai_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        if not isinstance(payload, dict):
            return out
        # Subject passthrough si viene
        subj = payload.get("subject")
        if isinstance(subj, dict):
            out["subject"] = {
                k: v for k, v in subj.items() if k in {"name", "code", "area", "hours"}
            }

                # Competencias técnicas: aceptar varias claves y formatos        # Competencias técnicas: aceptar varias claves y formatos
        comp_items = None
        if isinstance(payload.get("technical_competencies"), list):
            comp_items = payload.get("technical_competencies")
        else:
            for key in (
                "SubjectTechnicalCompetency",
                "technicalCompetencies",
                "TechnicalCompetencies",
                "competencias_tecnicas",
                "competenciasTecnicas",
                "competencias",
                "technical_competency",
            ):
                if isinstance(payload.get(key), list):
                    comp_items = payload.get(key)
                    break
        if comp_items is not None:
            items: List[Dict[str, Any]] = []
            # Acepta lista de strings o lista de objetos {number, description}
            for idx, it in enumerate(comp_items, start=1):
                if isinstance(it, dict):
                    try:
                        num = int(it.get("number") or idx)
                    except Exception:
                        num = idx
                    desc = str(it.get("description") or it.get("desc") or "").strip()
                else:
                    num = idx
                    desc = str(it or "").strip()
                if not desc:
                    continue
                items.append({"number": num, "description": desc})
                if len(items) >= 5:
                    break
            if items:
                out["technical_competencies"] = items
        # Unidades
        if "subject_units" in payload and isinstance(payload.get("subject_units"), list):
            out["subject_units"] = payload["subject_units"]
        else:
            alt_units = payload.get("SubjectUnit")
            # Caso dict con { unit_hours, units: [{name, hours}] }
            if isinstance(alt_units, dict) and isinstance(alt_units.get("units"), list):
                items: List[Dict[str, Any]] = []
                for idx, u in enumerate(alt_units["units"], start=1):
                    if not isinstance(u, dict):
                        continue
                    name = (u.get("name") or "").strip()
                    hours = u.get("hours")
                    try:
                        hours_int = int(hours) if hours is not None else None
                    except Exception:
                        hours_int = None
                    unit_obj: Dict[str, Any] = {"number": idx}
                    if name:
                        # Decision: map name â†’ expected_learning (objetivo breve)
                        unit_obj["expected_learning"] = name
                    if hours_int is not None:
                        unit_obj["unit_hours"] = hours_int
                    items.append(unit_obj)
                    if idx >= 4:
                        break
                if items:
                    out["subject_units"] = items
        # CompanyBoundaryCondition / API2 / API3 se mantendrán si la IA ya trae claves correctas
        for key in ("company_boundary_condition", "api_type_2_completion", "api_type_3_completion"):
            val = payload.get(key)
            if isinstance(val, dict):
                out[key] = val
                # Ajuste: coerción a texto para CBC y API2/API3\n        cbc = out.get("company_boundary_condition")\n        if isinstance(cbc, dict):\n            cbc["company_type_description"] = _coerce_to_text(cbc.get("company_type_description"))\n            cbc["company_requirements_for_level_2_3"] = _coerce_to_text(cbc.get("company_requirements_for_level_2_3"))\n            cbc["project_minimum_elements"] = _coerce_to_text(cbc.get("project_minimum_elements"))\n            out["company_boundary_condition"] = cbc\n        for blk in ("api_type_2_completion", "api_type_3_completion"):\n            dct = out.get(blk)\n            if isinstance(dct, dict):\n                for f in list(dct.keys()):\n                    dct[f] = _coerce_to_text(dct.get(f))\n                out[blk] = dct\n        return out\n\n    data = _normalize_ai_payload(data or {})
    # Pre-normalizar area a enum antes de validar
    try:
        subj_block = (data or {}).get("subject") or {}
        if isinstance(subj_block, dict) and subj_block.get("area") is not None:
            subj_block["area"] = map_area_name(subj_block.get("area"), env.get("default_area"))
            data["subject"] = subj_block
    except Exception:
        pass

    # Enriquecer/Construir SubjectUnit desde el PDF (evidencia, actividades, horas)
    pdf_units = _build_units_from_pdf(pdf_text)
    enriched_from_pdf: List[int] = []
    hours_found: Dict[str, int] = {}
    if pdf_units:
        for k, v in pdf_units.items():
            if isinstance(v, dict) and isinstance(v.get("unit_hours"), int):
                hours_found[k] = v["unit_hours"]
    existing_units = (data or {}).get("subject_units") or []
    if existing_units:
        num_map: Dict[int, Dict[str, Any]] = {}
        for it in existing_units:
            try:
                n = int(it.get("number"))
            except Exception:
                continue
            num_map[n] = dict(it)
        for ua_str, fields in (pdf_units or {}).items():
            try:
                n = int(ua_str)
            except Exception:
                continue
            u = num_map.get(n, {"number": n})
            changed = False
            for f in ("activities_description", "evaluation_evidence", "unit_hours"):
                if not u.get(f) and fields.get(f) is not None:
                    u[f] = fields.get(f)
                    changed = True
            if changed or n not in num_map:
                enriched_from_pdf.append(n)
            num_map[n] = u
        data["subject_units"] = [num_map[n] for n in sorted(num_map.keys()) if 1 <= n <= 4]
    else:
        units_list: List[Dict[str, Any]] = []
        for ua_str in sorted((pdf_units or {}).keys(), key=lambda x: int(x)):
            try:
                n = int(ua_str)
            except Exception:
                continue
            if not (1 <= n <= 4):
                continue
            obj = {"number": n}
            obj.update(pdf_units[ua_str])
            units_list.append(obj)
            enriched_from_pdf.append(n)
        if units_list:
            data["subject_units"] = units_list

    # Si no vienen unidades desde la IA, intentar parsearlas desde el texto extraido
    def _parse_units_from_text(text: Optional[str]) -> List[Dict[str, Any]]:
        if not text:
            return []
        import re
        t = text
        results: List[Dict[str, Any]] = []
        # Buscar cabeceras tipo "Unidad 1: Titulo ..." o variantes "U1 - Titulo"
        pattern = re.compile(r"(?:^|\n)\s*(?:Unidad|U)\s*(?P<num>[IVXLC0-9]{1,3})\s*[:\-â€“â€”]?\s*(?P<title>[^\n]*)", re.IGNORECASE)
        indices = [(m.start(), m.end(), m.group('num'), (m.group('title') or '').strip()) for m in pattern.finditer(t)]
        # Crear bloques por rango entre cabeceras
        for i, (s, e, num_raw, title) in enumerate(indices):
            blk = t[e: indices[i+1][0]] if i+1 < len(indices) else t[e:]
            # normalizar numero: romano o decimal
            num = None
            try:
                if num_raw.isdigit():
                    num = int(num_raw)
                else:
                    roman_map = {"I":1, "II":2, "III":3, "IV":4, "V":5, "VI":6, "VII":7, "VIII":8, "IX":9, "X":10}
                    num = roman_map.get(num_raw.upper(), None)
            except Exception:
                num = None
            if not num or not (1 <= num <= 4):
                continue
            # horas dentro del bloque
            hours = None
            for m in re.finditer(r"(?P<n>\d{1,3})\s*(horas|hrs\.?|h\.)", blk, flags=re.IGNORECASE):
                try:
                    val = int(m.group('n'))
                    if 1 <= val <= 200:
                        hours = max(hours or 0, val)
                except Exception:
                    pass
            # actividades: si el bloque contiene multiples lineas numeradas, conservarlas
            act = None
            lines = [ln.strip() for ln in blk.splitlines() if ln.strip()]
            num_lines = [ln for ln in lines if re.match(r"^\d+\.", ln)]
            if len(num_lines) >= 3:
                act = "\n".join(num_lines)
            obj: Dict[str, Any] = {"number": num}
            if title:
                obj["expected_learning"] = title
            if hours is not None:
                obj["unit_hours"] = hours
            if act:
                obj["activities_description"] = act
            results.append(obj)
            if len(results) >= 4:
                break
        # Fallback mejorado: agrupar bullets del tipo 1.1, 1.2, 1.3 como actividades de la Unidad 1; idem 2.x, 3.x, 4.x
        if not results:
            raw_lines = [ln.rstrip() for ln in t.splitlines()]
            bullet_re = re.compile(r"^\s*(?P<maj>\d{1,2})\.(?P<sub>\d{1,2})\s+(?P<text>.+)$")
            criteria_re = re.compile(r"^\s*\d+\.\d+\.\d+\b")
            header_re = re.compile(r"^(APRENDIZAJES|CRITERIOS|CONTENIDOS|ACTIVIDADES|ESTRATEGIAS|SISTEMA)\b", re.IGNORECASE)
            groups: Dict[int, List[str]] = {}
            i = 0
            while i < len(raw_lines):
                m = bullet_re.match(raw_lines[i])
                if not m:
                    i += 1
                    continue
                try:
                    maj = int(m.group("maj"))
                except Exception:
                    i += 1
                    continue
                if not (1 <= maj <= 4):
                    i += 1
                    continue
                buf = [m.group("text").strip()]
                j = i + 1
                while j < len(raw_lines):
                    ln = raw_lines[j].strip()
                    if not ln:
                        break
                    if bullet_re.match(raw_lines[j]) or criteria_re.match(ln) or header_re.match(ln):
                        break
                    buf.append(ln)
                    j += 1
                text_item = " ".join(s for s in buf if s)
                if text_item:
                    groups.setdefault(maj, []).append(text_item)
                i = j
            # construir unidades 1..4 a partir de grupos (sin continuaciones multilÃ­nea)
            def _shorten(s: str, limit: int = 220) -> str:
                if len(s) <= limit:
                    return s
                # corta en el primer punto razonable
                dot = s.find('.')
                if 60 <= dot <= limit:
                    return s[:dot+1].strip()
                return (s[:limit].rstrip() + 'â€¦')
            for maj in sorted([k for k in groups.keys() if 1 <= k <= 4])[:4]:
                items = groups.get(maj) or []
                if not items:
                    continue
                expected = _shorten(items[0].strip())
                activities = "\n".join(f"{i+1}. {it}" for i, it in enumerate(items)) if len(items) >= 2 else None
                obj: Dict[str, Any] = {"number": maj}
                if expected:
                    obj["expected_learning"] = expected
                if activities:
                    obj["activities_description"] = activities
                results.append(obj)
            # Si aun no hay resultados, como ultimo recurso: 1.,2.,3.,4. (tomando lineas completas)
            if not results:
                simple_re = re.compile(r"^\s*(?P<num>\d{1})\.\s+(?P<text>.+)")
                seen = set()
                for ln in lines:
                    m = simple_re.match(ln)
                    if not m:
                        continue
                    try:
                        n = int(m.group("num"))
                    except Exception:
                        continue
                    if not (1 <= n <= 4) or n in seen:
                        continue
                    seen.add(n)
                    results.append({"number": n, "expected_learning": m.group("text").strip()})
                results = results[:4]
        return results

    if not (data.get("subject_units") or []):
        parsed_units = _parse_units_from_text(pdf_text)
        if parsed_units:
            data["subject_units"] = parsed_units

    # Completar expected_learning desde titulos/agrupaciones si falta
    try:
        title_units = _parse_units_from_text(pdf_text) or []
        if (data or {}).get("subject_units"):
            title_map = {}
            for u in title_units:
                try:
                    n = int(u.get("number"))
                except Exception:
                    continue
                el = (u or {}).get("expected_learning")
                if el:
                    title_map[n] = el
            if title_map:
                for u in data["subject_units"]:
                    try:
                        n = int(u.get("number"))
                    except Exception:
                        continue
                    if not u.get("expected_learning") and n in title_map:
                        u["expected_learning"] = title_map[n]
    except Exception:
        pass

    schema = get_json_schema()
    ok = True
    error_msg = None
    try:
        if data:
            jsonschema_validate(instance=data, schema=schema)
    except ValidationError as ve:
        ok = False
        error_msg = str(ve)

    # Sin segunda pasada: una sola llamada a la IA local para priorizar velocidad

    # (moved helpers defined earlier)

    def _sanitize_expected_learning(text: Optional[str]) -> Optional[str]:
        if text is None:
            return None
        s = str(text).strip()
        if not s:
            return None
        # Cortar si aparecen encabezados o bloques no deseados pegados
        stops = [
            "APRENDIZAJES ESPERADOS",
            "CRITERIOS DE EVALU",
            "CONTENIDOS MÃNIMOS",
            "CONTENIDOS MINIMOS",
            "ACTIVIDADES MÃNIMAS",
            "ACTIVIDADES MINIMAS",
            "ESTRATEGIAS",
            "SISTEMA DE EVALU",
            "KEYBOARD_ARROW_DOWN",
            "UA ",
        ]
        up = s.upper()
        cut = len(s)
        for stop in stops:
            i = up.find(stop)
            if i != -1:
                cut = min(cut, i)
        # Cortar antes de numerales de criterios tipo 1.1.1, 2.1.3, etc.
        import re
        mcrit = re.search(r"\b\d+\.\d+\.\d+\b", s)
        if mcrit:
            cut = min(cut, mcrit.start())
        s = s[:cut].strip()
        # Si aÃºn es muy largo, corta a la primera oraciÃ³n razonable o a 220 chars
        if len(s) > 240:
            dot = s.find('.')
            if 40 <= dot <= 240:
                s = s[:dot+1].strip()
            else:
                s = (s[:240].rstrip() + 'â€¦')
        return s or None

    # No bloquear por fallo de schema: seguir usando el payload
    subj_payload = (data or {}).get("subject")
    subj_name = _maybe_titlecase(_norm_ws((subj_payload or {}).get("name")))
    subj_name = _sanitize_subject_name(subj_name)
    subj_code = _norm_code((subj_payload or {}).get("code"))

    # Resolve hours for Subject
    def _parse_hours_from_text(text: Optional[str]) -> Optional[int]:
        if not text:
            return None
        import re
        t = " ".join(text.split()).lower()
        # Prefer patterns with context first
        patterns = [
            r"horas\s*totales\s*(del|de la)?\s*(curso|asignatura)?\s*[:\-]?\s*(?P<n>\d{1,3})",
            r"total\s*de\s*horas\s*[:\-]?\s*(?P<n>\d{1,3})",
            r"horas\s*de\s*la\s*asignatura\s*[:\-]?\s*(?P<n>\d{1,3})",
            r"duraci[oÃ³]n\s*[:\-]?\s*(?P<n>\d{1,3})\s*(horas|hrs\.?|h\.)",
            r"(?P<n>\d{1,3})\s*(horas|hrs\.?|h\.)(\s*(cronol[oÃ³]gicas|pedag[oÃ³]gicas))?",
            r"horas\s*(cronol[oÃ³]gicas|pedag[oÃ³]gicas)\s*[:\-]?\s*(?P<n>\d{1,3})",
            r"hrs\.?\s*[:\-]?\s*(?P<n>\d{1,3})",
        ]
        candidates: List[int] = []
        for pat in patterns:
            for m in re.finditer(pat, t, flags=re.IGNORECASE):
                try:
                    val = int(m.group('n'))
                    if 4 <= val <= 500:
                        candidates.append(val)
                except Exception:
                    continue
            if candidates:
                break
        if not candidates:
            return None
        # Heuristic: choose the max reasonable number (e.g., 54 over 9)
        return max(candidates)

    ia_hours = None
    try:
        ia_hours = int((subj_payload or {}).get("hours")) if (subj_payload or {}).get("hours") is not None else None
    except Exception:
        ia_hours = None
    units = (data or {}).get("subject_units") or []
    sum_units = None
    try:
        vals = [int(u.get("unit_hours")) for u in units if u.get("unit_hours") is not None]
        sum_units = sum(vals) if vals else None
    except Exception:
        sum_units = None
    parsed_hours = _parse_hours_from_text(pdf_text)
    chosen_hours = ia_hours or sum_units or parsed_hours or int(env.get("default_hours"))

    # Trace how code was resolved for debugging/auditorÃ­a
    code_trace: Dict[str, Any] = {
        "ia_code": subj_code,
        "near_name_code": None,
        "global_code": None,
        "filename_code": None,
        "chosen_code": None,
        "appeared_in_text": None,
    }

    # Validar que el cÃ³digo aparezca en el texto; si no, reintentar heurÃ­sticas mÃ¡s cercanas al nombre
    def _code_in_text(code: Optional[str], raw: Optional[str]) -> bool:
        if not code or not raw:
            return False
        t = " ".join(raw.split()).lower()
        return code.lower() in t

    if subj_code is not None:
        code_trace["appeared_in_text"] = _code_in_text(subj_code, pdf_text)
    if subj_code and not code_trace["appeared_in_text"]:
        # Try near the detected name first
        nn = extract_code_from_text_near_name(pdf_text or "", subj_name)
        code_trace["near_name_code"] = nn
        gc = None
        if not nn:
            gc = extract_code_from_text(pdf_text or "")
            code_trace["global_code"] = gc
        fc = None
        if not (nn or gc) and getattr(d.file, 'name', None):
            import re
            base = d.file.name.replace('\\','/').rsplit('/', 1)[-1].rsplit('.', 1)[0]
            m = re.search(r"\((?P<code>[A-Za-z0-9\-]{3,})\)$", base)
            if m:
                fc = m.group('code')
                code_trace["filename_code"] = fc
        new_code = nn or gc or fc
        if new_code and _code_in_text(new_code, pdf_text):
            subj_code = _norm_code(new_code)
            code_trace["chosen_code"] = subj_code
            code_trace["appeared_in_text"] = True
            data = {**(data or {}), "subject": {**((data or {}).get("subject") or {}), "code": subj_code}}
        else:
            code_trace["chosen_code"] = subj_code

    # Collect simple diagnostics for units
    units_diag = {
        "provided": len((data or {}).get("subject_units") or []),
        "sum_unit_hours": sum_units,
        "parsed_hours": parsed_hours,
    }
    if 'enriched_from_pdf' in locals() and enriched_from_pdf:
        units_diag.update({
            "enriched_from_pdf": sorted(enriched_from_pdf),
            "hours_found": hours_found,
        })

    meta_update.update({
        "ai": {
            "schema_version": env.get("schema_version"),
            "model": (usage or {}).get("model") if isinstance(usage, dict) else env.get("model"),
            "usage": usage,
            "extractor": "pymupdf" if fitz else "unknown",
            "code_trace": code_trace,
            "hours_trace": {
                "ia_hours": ia_hours,
                "units_sum": sum_units,
                "parsed_from_text": parsed_hours,
                "chosen": chosen_hours,
            },
            "units": units_diag,
        },
        "error": error_msg,
    })

    # If we cannot reliably create Subject, skip
    if not subj_name or not subj_code:
        # 2) Segunda pasada: solo subject desde texto inline
        minimal, usage2 = extractor.extract_subject_minimal_from_text(pdf_text or "")
        msubj = (minimal or {}).get("subject") or {}
        ms_name = (msubj or {}).get("name")
        ms_code = (msubj or {}).get("code")

        # Fallback: parse from filename 'Name (CODE)'
        if (not ms_name or not ms_code) and getattr(d.file, 'name', None):
            import re
            fname = d.file.name.rsplit('/', 1)[-1]
            base = fname.rsplit('.', 1)[0]
            m = re.search(r"^(?P<name>.+?)\s*\((?P<code>[A-Za-z0-9\-]{3,})\)$", base)
            if m:
                ms_name = ms_name or m.group('name').strip()
                ms_code = ms_code or m.group('code').strip()

        if ms_name and ms_code:
            subj_name, subj_code = _maybe_titlecase(_norm_ws(ms_name)), _norm_code(ms_code)
            data = {**(data or {}), "subject": {**((data or {}).get("subject") or {}), "name": subj_name, "code": subj_code}}
        else:
            # 3rd fallback: parse from local PDF text
            _pair = extractor.extract_name_code_from_pdf(d.file.path)
            if _pair is None:
                loc_name, loc_code = None, None
            else:
                loc_name, loc_code = _pair
            if loc_name and loc_code:
                subj_name, subj_code = _maybe_titlecase(_norm_ws(loc_name)), _norm_code(loc_code)
                data = {**(data or {}), "subject": {**((data or {}).get("subject") or {}), "name": subj_name, "code": subj_code}}
                meta_update.setdefault("ai", {}).update({"local_text_fallback": True})
            else:
                # 4th fallback: match subject name from pool + code regex from full text cache
                pool_name = _match_subject_name_local(d.text_cache or "")
                # Intentar cÃ³digo cerca del nombre detectado; si falla, bÃºsqueda global
                code_guess = extract_code_from_text_near_name(d.text_cache or "", pool_name) or extract_code_from_text(d.text_cache or "")
                if not pool_name or not code_guess:
                    meta_update["status"] = "skipped_missing_subject"
                    # include extract payloads to help debug
                    debug_meta = {**meta_update, "extract": data or {}, "extract_minimal": minimal or {}}
                    d.meta = {**(d.meta or {}), **debug_meta}
                    d.processed_at = timezone.now()
                    d.save(update_fields=["meta", "processed_at"])
                    logger.warning("Descriptor %s skipped: missing subject name/code; file=%s", d.id, getattr(d.file, 'name', ''))
                    # Optional deletion
                    delete_on_skip = str(env.get("delete_on_skip", "true")).lower() in {"1","true","yes","on"}
                    if delete_on_skip:
                        try:
                            if d.file:
                                d.file.delete(save=False)
                            did = d.id
                            d.delete()
                            logger.info("Descriptor %s deleted after skip.", did)
                        except Exception as e:
                            logger.error("Failed to delete skipped descriptor %s: %s", d.id, e)
                    return None
                subj_name, subj_code = _maybe_titlecase(_norm_ws(pool_name)), _norm_code(code_guess)
                data = {**(data or {}), "subject": {**((data or {}).get("subject") or {}), "name": subj_name, "code": subj_code}}

    with transaction.atomic():
        # Area
        # Infer area: priority by subject name mapping, subject code heuristics, then raw/AI area mapping
        area_name = subject_area_for_name(subj_name) or area_by_code(subj_code) or map_area_name((subj_payload or {}).get("area"), env.get("default_area"))
        if area_name not in AREA_ENUM:
            area_name = env.get("default_area")
        area_obj, _ = Area.objects.get_or_create(name=area_name)

        # Semester
        semester_name = env.get("default_semester")
        semester_obj, _ = SemesterLevel.objects.get_or_create(name=semester_name)

        # Subject (create or update, then link back to descriptor if missing)
        subject, _ = Subject.objects.update_or_create(
            code=subj_code,
            section=str(env.get("default_section")),
            defaults={
                "name": subj_name,
                "area": area_obj,
                "semester": semester_obj,
                "campus": env.get("default_campus"),
                "api_type": int(env.get("default_api_type")),
                "hours": int(chosen_hours),
            },
        )

        if d.subject_id is None:
            # Enforce unique descriptor per subject: si ya existe, no sobreescribir; dejar registro para revisiÃ³n
            existing = DescriptorFile.objects.filter(subject=subject).exclude(id=d.id).first()
            if existing is not None:
                meta_conflict = {**(d.meta or {}), "status": "conflict_existing_descriptor", "subject_id": subject.id}
                d.meta = meta_conflict
                d.processed_at = timezone.now()
                d.save(update_fields=["meta", "processed_at"])
                logger.info("Descriptor %s not linked: subject %s already has a descriptor (kept current record)", d.id, subject.id)
            else:
                d.subject = subject
                d.save(update_fields=["subject"])

        # Si faltan bloques no-unitarios, reintentar secciones desde texto antes de persistir
        if not ((data or {}).get("technical_competencies") and (data or {}).get("company_boundary_condition") and ((data or {}).get("api_type_2_completion") or (data or {}).get("api_type_3_completion"))):
            try:
                sec2, _u2 = extractor.extract_sections_from_text(
                    pdf_text or "",
                    need_cbc=True,
                    need_api2=True,
                    need_api3=True,
                    need_competencies=True,
                )
                if isinstance(sec2, dict):
                    if sec2.get("technical_competencies") and not (data or {}).get("technical_competencies"):
                        data["technical_competencies"] = sec2.get("technical_competencies")
                    if sec2.get("company_boundary_condition") and not (data or {}).get("company_boundary_condition"):
                        data["company_boundary_condition"] = sec2.get("company_boundary_condition")
                    if sec2.get("api_type_2_completion") and not (data or {}).get("api_type_2_completion"):
                        data["api_type_2_completion"] = sec2.get("api_type_2_completion")
                    if sec2.get("api_type_3_completion") and not (data or {}).get("api_type_3_completion"):
                        data["api_type_3_completion"] = sec2.get("api_type_3_completion")
            except Exception:
                pass

        # Technical Competencies (1..5)
        for item in (data or {}).get("technical_competencies", []) or []:
            try:
                num = int(item.get("number"))
            except Exception:
                continue
            desc = _norm_ws(item.get("description")) or ""
            if not (1 <= num <= 5) or not desc:
                continue
            SubjectTechnicalCompetency.objects.update_or_create(
                subject=subject,
                number=num,
                defaults={"description": desc},
            )

        # Company Boundary Condition
        cbc = (data or {}).get("company_boundary_condition") or {}
        if cbc:
            CompanyBoundaryCondition.objects.update_or_create(
                subject=subject,
                defaults={
                    "company_type_description": _norm_ws(cbc.get("company_type_description")) or "",
                    "company_requirements_for_level_2_3": _norm_ws(cbc.get("company_requirements_for_level_2_3")) or "",
                    "project_minimum_elements": _norm_ws(cbc.get("project_minimum_elements")) or "",
                },
            )

        # API Type 2
        api2 = (data or {}).get("api_type_2_completion") or {}
        if api2:
            ApiType2Completion.objects.update_or_create(
                subject=subject,
                defaults={
                    "project_goal_students": _norm_ws(api2.get("project_goal_students")) or "",
                    "deliverables_at_end": _norm_ws(api2.get("deliverables_at_end")) or "",
                    "company_expected_participation": _norm_ws(api2.get("company_expected_participation")) or "",
                    "other_activities": _norm_ws(api2.get("other_activities")) or "",
                },
            )

        # API Type 3
        api3 = (data or {}).get("api_type_3_completion") or {}
        if api3:
            ApiType3Completion.objects.update_or_create(
                subject=subject,
                defaults={
                    "project_goal_students": _norm_ws(api3.get("project_goal_students")) or "",
                    "deliverables_at_end": _norm_ws(api3.get("deliverables_at_end")) or "",
                    "expected_student_role": _norm_ws(api3.get("expected_student_role")) or "",
                    "other_activities": _norm_ws(api3.get("other_activities")) or "",
                    "master_guide_expected_support": _norm_ws(api3.get("master_guide_expected_support")) or "",
                },
            )

        # Subject Units (1..4)
        units_saved = 0
        for item in (data or {}).get("subject_units", []) or []:
            try:
                num = int(item.get("number"))
            except Exception:
                continue
            if not (1 <= num <= 4):
                continue

            # No sobrescribir con None ni pisar campos ya llenados manualmente
            unit, _ = SubjectUnit.objects.get_or_create(subject=subject, number=num)

            val_expected = _sanitize_expected_learning(_norm_ws(item.get("expected_learning"))) if item.get("expected_learning") is not None else None
            val_hours = None
            if item.get("unit_hours") is not None:
                try:
                    val_hours = int(item.get("unit_hours") or 0)
                except Exception:
                    val_hours = None
            val_activities = _norm_ws(item.get("activities_description")) if item.get("activities_description") is not None else None
            val_evidence = _norm_ws(item.get("evaluation_evidence")) if item.get("evaluation_evidence") is not None else None

            changed = False
            if val_expected and not (unit.expected_learning and unit.expected_learning.strip()):
                unit.expected_learning = val_expected
                changed = True
            if (val_hours is not None) and (unit.unit_hours is None):
                unit.unit_hours = val_hours
                changed = True
            if val_activities and not (unit.activities_description and unit.activities_description.strip()):
                unit.activities_description = val_activities
                changed = True
            if val_evidence and not (unit.evaluation_evidence and unit.evaluation_evidence.strip()):
                unit.evaluation_evidence = val_evidence
                changed = True

            if changed:
                unit.save()
                units_saved += 1

        # Reflect unit save stats in meta
        meta_update.setdefault("ai", {}).setdefault("units", {}).update({
            "saved": units_saved,
        })

    meta_update["status"] = meta_update.get("status") or ("ok" if ok else "invalid_schema")
    d.meta = {**(d.meta or {}), **meta_update, "extract": data or {}, "text_chars": len(pdf_text or "")}
    d.processed_at = timezone.now()
    d.save(update_fields=["meta", "processed_at"])

    return d.id








