from pathlib import Path
from ingestors import ingest_pdf_bytes, ingest_txt_bytes, ingest_docx_bytes

# OPTION A: absolute path (raw string)
p = Path(r"C:\Users\joshu\Downloads\frontier_ai_objective_primer.pdf")

if not p.exists():
    raise SystemExit(f"File not found: {p}")

if p.suffix.lower() == ".pdf":
    n = ingest_pdf_bytes(p.read_bytes(), p.name, 1200)
elif p.suffix.lower() == ".txt":
    n = ingest_txt_bytes(p.read_bytes(), p.name, 1200)
elif p.suffix.lower() == ".docx":
    n = ingest_docx_bytes(p.read_bytes(), p.name, 1200)
else:
    raise SystemExit(f"Unsupported file type: {p.suffix}")

print(f"Ingested {n} chunks from {p}")
