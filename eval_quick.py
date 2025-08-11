import json
import time
import statistics as stats
from pathlib import Path
from rag_chain import answer
from memory_backend import search

seed = [
    {
        "q": "What is the project’s 18–24 month objective?",
        "expect": ["frontier", "equity", "proximity"],
    },
    {
        "q": "How do I add a new memory and verify retrieval?",
        "expect": ["sidebar", "retrieve", "score", "id"],
    },
    {
        "q": "What does a higher retrieval score indicate here?",
        "expect": ["closer", "match", "relevant"],
    },
    {
        "q": "Where are weekly public artifacts referenced?",
        "expect": ["weekly", "artifact"],
    },
    {
        "q": "Which embedding model and vector DB are used?",
        "expect": ["text-embedding-3-small", "Pinecone"],
    },
]

results = []
for row in seed:
    t0 = time.time()
    ctx_docs = [d for _, d, *_ in search(row["q"], k=5)]
    resp, _ = answer(row["q"], k=5)
    dt = (time.time() - t0) * 1000
    blob = " ".join(ctx_docs).lower()
    recall = all(x.lower() in blob for x in row["expect"])
    answer_ok = all(x.lower() in resp.lower() for x in row["expect"])
    results.append(
        {
            "q": row["q"],
            "recall": recall,
            "answer_ok": answer_ok,
            "latency_ms": round(dt, 1),
        }
    )

summary = {
    "n": len(results),
    "recall_rate": round(sum(r["recall"] for r in results) / len(results), 3),
    "answer_rate": round(sum(r["answer_ok"] for r in results) / len(results), 3),
    "latency_ms_avg": round(stats.mean([r["latency_ms"] for r in results]), 1),
}
Path("eval_report.json").write_text(
    json.dumps({"summary": summary, "results": results}, indent=2), encoding="utf-8"
)
print(json.dumps(summary, indent=2))
