from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell
import unicodedata
import json
from django.http import HttpResponse
from pathlib import Path


def _normalize_coord(coord: str) -> str:
    """
    Accept a single cell (e.g. "C5") or a range (e.g. "C5:D5").
    Return the top-left coordinate (e.g. "C5").
    """
    if not coord:
        return coord
    coord = str(coord).strip()
    if ":" in coord:
        start, _ = coord.split(":", 1)
        return start.strip()
    return coord


def _set_value_safe(ws, coord: str, value):
    coord = _normalize_coord(coord)
    cell = ws[coord]
    # If targeting a merged cell that is not the top-left anchor, redirect
    if isinstance(cell, MergedCell):
        for rng in ws.merged_cells.ranges:
            if coord in rng:
                anchor = ws.cell(row=rng.min_row, column=rng.min_col)
                anchor.value = value
                return
        # If not found in ranges (edge case), just skip silently
        return
    cell.value = value


def export_form_to_xlsx(form, template_path: str):
    wb = load_workbook(filename=template_path)
    ws = wb.active

    # Prefer mapping defined en DB (FormTemplate.schema.xlsx_mapping)
    def _norm(s: str) -> str:
        if s is None:
            return ""
        s = str(s)
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = s.lower().strip()
        return s.replace(":", "")

    def _find_label_cell(sheet, label_norm: str):
        max_row, max_col = sheet.max_row, sheet.max_column
        for r in range(1, max_row + 1):
            for c in range(1, max_col + 1):
                v = sheet.cell(row=r, column=c).value
                if v is None:
                    continue
                vv = _norm(v)
                if vv == label_norm or label_norm in vv:
                    return r, c
        return None

    def _offset(rc, direction: str):
        if rc is None:
            return None
        r, c = rc
        if direction == "right":
            return r, c + 1
        if direction == "below":
            return r + 1, c
        return rc

    def _coord(rc):
        if rc is None:
            return None
        from openpyxl.utils import get_column_letter
        r, c = rc
        return f"{get_column_letter(c)}{r}"

    # 1) Try JSON mapping co-located with the Excel template (authoritative)
    mapping_path = get_mapping_path(form.template.key)
    json_mapping = None
    try:
        with open(mapping_path, "r", encoding="utf-8") as fh:
            json_mapping = json.load(fh)
    except Exception:
        json_mapping = None
    if isinstance(json_mapping, dict) and json_mapping:
        for field, cell in json_mapping.items():
            _set_value_safe(ws, str(cell), form.data.get(field, ""))
    else:
        # 2) Fallback to DB mapping in FormTemplate.schema.xlsx_mapping
        schema = getattr(form.template, "schema", {}) or {}
        xlsx_mapping = schema.get("xlsx_mapping")
        if isinstance(xlsx_mapping, list) and xlsx_mapping:
            for item in xlsx_mapping:
                field = item.get("field")
                if not field:
                    continue
                value = form.data.get(field, "")
                cell = item.get("cell")
                if cell:
                    _set_value_safe(ws, cell, value)
                    continue
                label = item.get("label")
                direction = item.get("direction", "right")
                if label:
                    rc = _find_label_cell(ws, _norm(label))
                    target = _coord(_offset(rc, direction))
                    if target:
                        _set_value_safe(ws, target, value)

    resp = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    filename = f"{form.subject.code}-{form.template.key}.xlsx"
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(resp)
    return resp


def get_template_path(form_template_key: str) -> str:
    base = Path(__file__).resolve().parent / "templates" / "excel"
    files = {
        "ficha-api": "ficha_api.xlsx",
        "proyecto-api": "proyecto_api.xlsx",
    }
    return str(base / files[form_template_key])


def get_mapping_path(form_template_key: str) -> str:
    base = Path(__file__).resolve().parent / "templates" / "excel"
    files = {
        "ficha-api": "ficha_api_celdas_de_respuestas_mapeadas.json",
        "proyecto-api": "proyecto_api_celdas_de_respuestas_mapeadas.json",
    }
    return str(base / files[form_template_key])
