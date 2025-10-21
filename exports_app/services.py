from openpyxl import load_workbook
from django.http import HttpResponse
from pathlib import Path

def export_form_to_xlsx(form, template_path: str):
    wb = load_workbook(filename=template_path)
    ws = wb.active

    # TODO: mapea campos → celdas según tu plantilla institucional
    mapping = {
        "asignatura_codigo": "B2",
        "asignatura_nombre": "B3",
        "sistema_evaluacion": "B20",
        # …
    }
    for field, cell in mapping.items():
        ws[cell] = form.data.get(field, "")

    resp = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    filename = f"{form.subject.code}-{form.template.key}.xlsx"
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(resp)
    return resp

def get_template_path(form_template_key: str) -> str:
    base = Path(__file__).resolve().parent / "templates" / "excel"
    # coloca tus archivos reales aquí:
    files = {
        "ficha-api": "Ficha API P2025 Ejemplo.xlsx",
        "proyecto-api": "PROYECTO API P2025 ejemplo.xlsx",
    }
    return str(base / files[form_template_key])