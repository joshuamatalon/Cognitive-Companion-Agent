# ingestors.py
from pypdf import PdfReader
from docx import Document
from vec_memory import upsert_many
from io import BytesIO
import pathlib


def _chunks(blob: str, n: int = 1200):
    blob = blob.replace("\x00", "")
    return [
        blob[i : i + n].strip()
        for i in range(0, len(blob), n)
        if blob[i : i + n].strip()
    ]


def ingest_pdf_bytes(b: bytes, name: str, chunk_chars: int = 1200) -> int:
    pages = [(p.extract_text() or "") for p in PdfReader(BytesIO(b)).pages]
    parts = _chunks("\n".join(pages), chunk_chars)
    upsert_many(parts, {"type": "pdf", "source": pathlib.Path(name).name})
    return len(parts)


def ingest_txt_bytes(b: bytes, name: str, chunk_chars: int = 1200) -> int:
    parts = _chunks(b.decode("utf-8", errors="ignore"), chunk_chars)
    upsert_many(parts, {"type": "txt", "source": pathlib.Path(name).name})
    return len(parts)


def ingest_docx_bytes(b: bytes, name: str, chunk_chars: int = 1200) -> int:
    doc = Document(BytesIO(b))
    text = "\n".join([p.text or "" for p in doc.paragraphs])
    parts = _chunks(text, chunk_chars)
    upsert_many(parts, {"type": "docx", "source": pathlib.Path(name).name})
    return len(parts)
