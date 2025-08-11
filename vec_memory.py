# vec_memory.py
import os
import uuid
from typing import List, Tuple, Dict, Any

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from utils_log import append_log
from config import config

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIM = int(os.getenv("EMBED_DIM", "1536"))
INDEX_NAME = os.getenv("PINECONE_INDEX", "cca-memories")
PINECONE_ENV = config.PINECONE_ENV

# Initialize clients only if config is valid
if config.is_valid():
    oa = OpenAI(api_key=config.OPENAI_API_KEY)
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    
    # Ensure index exists
    existing = {i["name"] for i in pc.list_indexes().get("indexes", [])}
    if INDEX_NAME not in existing:
        try:
            pc.create_index(
                name=INDEX_NAME,
                dimension=EMBED_DIM,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV),
            )
        except Exception:
            pass  # index may be creating already
    
    index = pc.Index(INDEX_NAME)
else:
    oa = None
    pc = None
    index = None
    print("⚠️  API clients not initialized due to configuration errors")


def _embed(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    resp = oa.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


# --- public API ---


def upsert_note(text: str, meta: Dict[str, Any] | None = None) -> str:
    _id = str(uuid.uuid4())
    vec = _embed([text])[0]
    index.upsert(
        vectors=[{"id": _id, "values": vec, "metadata": {"text": text, **(meta or {})}}]
    )
    append_log("upsert", {"id": _id, "meta": (meta or {}), "len": len(text)})
    return _id


def upsert_many(chunks: List[str], meta: Dict[str, Any]) -> List[str]:
    if not chunks:
        return []
    ids: List[str] = []
    B = 100
    for i in range(0, len(chunks), B):
        batch = chunks[i : i + B]
        vecs = _embed(batch)
        batch_ids = [str(uuid.uuid4()) for _ in batch]
        index.upsert(
            vectors=[
                {"id": bi, "values": v, "metadata": {"text": t, **meta}}
                for bi, v, t in zip(batch_ids, vecs, batch)
            ]
        )
        for bi, t in zip(batch_ids, batch):
            append_log("upsert", {"id": bi, "meta": meta, "len": len(t)})
        ids.extend(batch_ids)
    return ids


def search(query: str, k: int = 5) -> List[Tuple[str, str, Dict[str, Any]]]:
    """Return [(id, text, metadata)]"""
    qv = _embed([query])[0]
    res = index.query(vector=qv, top_k=max(1, k), include_metadata=True)
    out: List[Tuple[str, str, Dict[str, Any]]] = []
    for m in getattr(res, "matches", []):
        meta = dict(getattr(m, "metadata", {}) or {})
        txt = meta.pop("text", "")
        out.append((m.id, txt, meta))
    return out


def search_scores(
    query: str, k: int = 5
) -> List[Tuple[str, str, Dict[str, Any], float]]:
    """Return [(id, text, metadata, score)]"""
    qv = _embed([query])[0]
    res = index.query(vector=qv, top_k=max(1, k), include_metadata=True)
    out: List[Tuple[str, str, Dict[str, Any], float]] = []
    for m in getattr(res, "matches", []):
        meta = dict(getattr(m, "metadata", {}) or {})
        txt = meta.pop("text", "")
        score = float(getattr(m, "score", 0.0))
        out.append((m.id, txt, meta, score))
    return out


def delete_by_ids(ids: List[str], namespace: str | None = None) -> Dict[str, Any]:
    if not ids:
        return {"deleted": 0}
    try:
        index.delete(ids=ids, namespace=namespace)
        append_log("delete", {"ids": ids, "namespace": namespace})
        return {"deleted": len(ids)}
    except Exception as e:
        return {"deleted": 0, "error": str(e)}


def export_all() -> List[Dict[str, Any]]:
    """Return a simple dump of all items (id, text, metadata)."""
    # Pinecone v5 does not support full scans without an iterator; this is a stub.
    return []


def reset_all():
    """Recreate the index fresh."""
    try:
        pc.delete_index(INDEX_NAME)
    except Exception:
        pass
    pc.create_index(
        name=INDEX_NAME,
        dimension=EMBED_DIM,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV),
    )
