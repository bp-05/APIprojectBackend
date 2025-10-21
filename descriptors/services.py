import pdfplumber

def extract_text_tables(path: str):
    text, tables = [], []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text() or "")
            for t in (page.extract_tables() or []):
                tables.append(t)
    return "\n".join(text), tables, {"pages": len(text), "tables": len(tables)}