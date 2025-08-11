# pdf_ingest.py
from pypdf import PdfReader
from vec_memory import upsert_note
from io import BytesIO
import pathlib


def ingest_pdf_bytes(file_bytes: bytes, filename: str, chunk_chars: int = 1200):
    reader = PdfReader(BytesIO(file_bytes))
    text = []
    for p in reader.pages:
        text.append(p.extract_text() or "")
    blob = "\n".join(text)

    total = 0
    for i in range(0, len(blob), chunk_chars):
        chunk = blob[i : i + chunk_chars].strip()
        if chunk:
            upsert_note(chunk, {"type": "pdf", "source": pathlib.Path(filename).name})
            total += 1
    return total  # <— number of chunks stored
