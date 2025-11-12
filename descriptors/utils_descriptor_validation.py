from typing import Optional
import os
import re

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None

from .ai_service import extract_code_from_text, extract_code_from_text_near_name, AIExtractor
from typing import Optional


def _norm_code(code: Optional[str]) -> Optional[str]:
    if code is None:
        return None
    c = "".join(ch for ch in str(code).strip() if ch.isalnum() or ch in {'-','_'})
    if not c:
        return None
    upper = str(os.environ.get('SUBJECT_CODE_UPPERCASE', 'true')).lower() in {'1','true','yes','on'}
    return c.upper() if upper else c.lower()


def _extract_code_from_upload(file_obj, subject_name: Optional[str] = None) -> Optional[str]:
    try:
        text = None
        if hasattr(file_obj, 'read') and fitz is not None:
            # file_obj puede ser UploadedFile o FileField; obtener bytes de manera no destructiva
            pos = None
            try:
                pos = file_obj.tell()
            except Exception:
                pos = None
            try:
                data = file_obj.read()
            finally:
                try:
                    if pos is not None:
                        file_obj.seek(pos)
                except Exception:
                    pass
            doc = fitz.open(stream=data, filetype='pdf')
            try:
                parts = []
                max_pages = min(30, doc.page_count)
                for i in range(max_pages):
                    try:
                        parts.append(doc.load_page(i).get_text('text') or '')
                    except Exception:
                        break
                text = "\n".join(parts)
            finally:
                doc.close()
        elif getattr(file_obj, 'path', None):
            # Tiene ruta (FileField existente)
            if fitz is not None:
                doc = fitz.open(file_obj.path)
                try:
                    parts = []
                    max_pages = min(30, doc.page_count)
                    for i in range(max_pages):
                        try:
                            parts.append(doc.load_page(i).get_text('text') or '')
                        except Exception:
                            break
                    text = "\n".join(parts)
                finally:
                    doc.close()
        if not text:
            return None
        name_hint = (subject_name or '').strip() or None
        code = extract_code_from_text_near_name(text, name_hint) if name_hint else None
        code = code or extract_code_from_text(text)
        return _norm_code(code)
    except Exception:
        return None


def extract_code_from_path_robust(
    file_path: Optional[str],
    subject_name: Optional[str] = None,
    file_name: Optional[str] = None,
) -> Optional[str]:
    """Robust code extraction using the same logic path as tasks:
    - Prefer AIExtractor.extract_name_code_from_pdf(path)
    - Fallback to reading text and using near-name/global regex heuristics
    """
    if not file_path:
        return None
    try:
        extractor = AIExtractor()
    except Exception:
        extractor = None  # type: ignore
    # Try AI extractor first
    try:
        if extractor is not None and file_path:
            nm, cd = extractor.extract_name_code_from_pdf(file_path)
            if cd:
                return _norm_code(cd)
    except Exception:
        pass
    # Fallback: read text and apply regex heuristics
    try:
        if fitz is not None and file_path:
            doc = fitz.open(file_path)
            try:
                parts = []
                max_pages = min(30, doc.page_count)
                for i in range(max_pages):
                    try:
                        parts.append(doc.load_page(i).get_text('text') or '')
                    except Exception:
                        break
                text = "\n".join(parts)
            finally:
                doc.close()
        else:
            text = None
    except Exception:
        text = None
    if not text:
        text = None
    name_hint = (subject_name or '').strip() or None
    code = None
    if text:
        code = extract_code_from_text_near_name(text, name_hint) if name_hint else None
        code = code or extract_code_from_text(text)
    if not code and file_name:
        try:
            base = os.path.basename(file_name)
            stem = os.path.splitext(base)[0]
            match = re.search(r"\((?P<code>[A-Za-z0-9\-]{3,})\)$", stem)
            if match:
                code = match.group('code')
        except Exception:
            pass
    return _norm_code(code) if code else None


def sanitize_subject_name(name: Optional[str]) -> Optional[str]:
    """Normalize a subject name extracted from PDF or filename.

    - If it contains '>' hierarchy, take the last meaningful segment.
    - Strip common headers like 'Asignaturas' or 'Administrador de Asignaturas y Programas de Estudio'.
    - Apply titlecase depending on SUBJECT_NAME_TITLECASE env var.
    """
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
    enabled = str(os.environ.get('SUBJECT_NAME_TITLECASE', 'true')).lower() in {'1','true','yes','on'}
    return s.title() if enabled else s
