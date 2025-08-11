# vec_memory.py
import os
import uuid
import time
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


def _embed(texts: List[str], max_retries: int = 3) -> List[List[float]]:
    """Create embeddings with retry logic."""
    if not texts:
        return []
    
    if not oa:
        raise RuntimeError("OpenAI client not initialized")
    
    for attempt in range(max_retries):
        try:
            resp = oa.embeddings.create(model=EMBED_MODEL, input=texts)
            return [d.embedding for d in resp.data]
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to create embeddings after {max_retries} attempts: {str(e)}")
            
            # Exponential backoff
            wait_time = (2 ** attempt) + (attempt * 0.1)
            print(f"Embedding attempt {attempt + 1} failed, retrying in {wait_time:.1f}s: {str(e)}")
            time.sleep(wait_time)
    
    return []


# --- public API ---


def upsert_note(text: str, meta: Dict[str, Any] | None = None) -> str:
    """Add a note to the vector database with error handling."""
    if not index:
        raise RuntimeError("Vector database not initialized")
    
    if not text or not text.strip():
        raise ValueError("Text content cannot be empty")
    
    try:
        _id = str(uuid.uuid4())
        vec = _embed([text.strip()])[0]
        
        # Retry upsert operation
        max_retries = 3
        for attempt in range(max_retries):
            try:
                index.upsert(
                    vectors=[{"id": _id, "values": vec, "metadata": {"text": text.strip(), **(meta or {})}}]
                )
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to upsert note after {max_retries} attempts: {str(e)}")
                time.sleep(0.5 * (attempt + 1))
        
        append_log("upsert", {"id": _id, "meta": (meta or {}), "len": len(text)})
        return _id
        
    except Exception as e:
        error_msg = f"Failed to add note: {str(e)}"
        append_log("error", {"operation": "upsert", "error": error_msg})
        raise RuntimeError(error_msg)


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
    """Return [(id, text, metadata, score)] with error handling."""
    if not index:
        raise RuntimeError("Vector database not initialized")
    
    if not query or not query.strip():
        return []
    
    try:
        qv = _embed([query.strip()])[0]
        
        # Retry search operation
        max_retries = 3
        for attempt in range(max_retries):
            try:
                res = index.query(vector=qv, top_k=max(1, k), include_metadata=True)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to search after {max_retries} attempts: {str(e)}")
                time.sleep(0.5 * (attempt + 1))
        
        out: List[Tuple[str, str, Dict[str, Any], float]] = []
        for m in getattr(res, "matches", []):
            try:
                meta = dict(getattr(m, "metadata", {}) or {})
                txt = meta.pop("text", "")
                score = float(getattr(m, "score", 0.0))
                out.append((m.id, txt, meta, score))
            except Exception as e:
                print(f"Warning: Error processing search result {m.id}: {e}")
                continue
        
        return out
        
    except Exception as e:
        error_msg = f"Search failed: {str(e)}"
        append_log("error", {"operation": "search", "query": query[:100], "error": error_msg})
        raise RuntimeError(error_msg)


def delete_by_ids(ids: List[str], namespace: str | None = None) -> Dict[str, Any]:
    if not ids:
        return {"deleted": 0}
    try:
        index.delete(ids=ids, namespace=namespace)
        append_log("delete", {"ids": ids, "namespace": namespace})
        return {"deleted": len(ids)}
    except Exception as e:
        return {"deleted": 0, "error": str(e)}


def get_memory_stats() -> Dict[str, Any]:
    """Get comprehensive memory statistics."""
    try:
        if not index:
            return {"error": "Vector database not initialized"}
        
        # Get index stats
        stats = index.describe_index_stats()
        total_vectors = stats.total_vector_count or 0
        
        # Get recent activity from log
        recent_activity = []
        try:
            from pathlib import Path
            import json
            log_file = Path("data/memory_log.jsonl")
            if log_file.exists():
                lines = log_file.read_text(encoding="utf-8").splitlines()
                for line in lines[-10:]:
                    try:
                        recent_activity.append(json.loads(line))
                    except:
                        continue
        except:
            pass
        
        # Calculate activity metrics
        activity_counts = {"upsert": 0, "delete": 0}
        for entry in recent_activity:
            event = entry.get("event", "unknown")
            if event in activity_counts:
                activity_counts[event] += 1
        
        return {
            "total_memories": total_vectors,
            "index_name": INDEX_NAME,
            "embedding_dimension": EMBED_DIM,
            "embedding_model": EMBED_MODEL,
            "recent_upserts": activity_counts["upsert"],
            "recent_deletes": activity_counts["delete"],
            "index_status": "healthy" if index else "unavailable",
            "last_updated": recent_activity[-1].get("timestamp") if recent_activity else None
        }
    except Exception as e:
        return {"error": f"Failed to get stats: {str(e)}"}

def export_all() -> List[Dict[str, Any]]:
    """Export all memories by querying with dummy vector."""
    try:
        if not index or not oa:
            return []
        
        # Create a dummy query vector to get all results
        dummy_text = "query all memories export"
        dummy_vector = _embed([dummy_text])[0]
        
        # Query with high top_k to get many results
        results = index.query(
            vector=dummy_vector,
            top_k=10000,  # Get up to 10k results
            include_metadata=True
        )
        
        export_data = []
        for match in results.matches:
            metadata = dict(match.metadata) if match.metadata else {}
            text = metadata.pop("text", "")
            
            export_data.append({
                "id": match.id,
                "text": text,
                "metadata": metadata,
                "score": float(match.score) if hasattr(match, 'score') else 0.0
            })
        
        return export_data
    except Exception as e:
        print(f"Export error: {e}")
        return []


def reset_all():
    """Clear all memories from the index."""
    if not index:
        raise RuntimeError("Vector database not initialized")
    
    try:
        # Method 1: Try to delete all vectors by getting all IDs first
        print("Attempting to clear all memories...")
        
        # Get all vector IDs by doing a broad query
        dummy_vector = [0.0] * EMBED_DIM  # Zero vector
        
        try:
            # Query to get all vectors (use high top_k)
            results = index.query(
                vector=dummy_vector,
                top_k=10000,  # Maximum we can get at once
                include_metadata=False  # We only need IDs
            )
            
            if results.matches:
                ids_to_delete = [match.id for match in results.matches]
                print(f"Found {len(ids_to_delete)} memories to delete")
                
                # Delete in batches of 1000 (Pinecone limit)
                batch_size = 1000
                for i in range(0, len(ids_to_delete), batch_size):
                    batch_ids = ids_to_delete[i:i + batch_size]
                    index.delete(ids=batch_ids)
                    print(f"Deleted batch {i//batch_size + 1}/{(len(ids_to_delete) + batch_size - 1)//batch_size}")
                    time.sleep(1)  # Small delay between batches
                
                print(f"Successfully deleted {len(ids_to_delete)} memories")
                
            else:
                print("No memories found to delete")
                
        except Exception as query_error:
            print(f"Query method failed: {query_error}")
            # Fallback: delete all vectors without getting IDs first
            print("Trying fallback method: delete all vectors")
            index.delete(delete_all=True)
            print("Fallback deletion completed")
        
        # Log the reset
        append_log("reset", {"method": "clear_all", "timestamp": time.time()})
        print("Reset completed successfully")
        
    except Exception as e:
        error_msg = f"Reset failed: {str(e)}"
        print(f"Error: {error_msg}")
        append_log("error", {"operation": "reset", "error": error_msg})
        raise RuntimeError(error_msg)
