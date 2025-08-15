"""
Test with unseen queries to verify we're not overfitting.
"""

import time
import json
import statistics as stats
from pathlib import Path
from search_enhancements import search
from rag_chain import answer

SEED_PATH = Path("eval_seed_unseen.jsonl")


def load_seed():
    if not SEED_PATH.exists():
        raise SystemExit(f"Create {SEED_PATH}")
    return [
        json.loads(line)
        for line in SEED_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def recall_ok(ctx_docs, expects):
    blob = " ".join(ctx_docs).lower()
    return all(x.lower() in blob for x in expects)


def answer_ok(resp, expects):
    text = resp.lower()
    return all(x.lower() in text for x in expects)


def run():
    print("=" * 60)
    print("UNSEEN QUERY EVALUATION - Testing Generalization")
    print("=" * 60)
    
    cases = load_seed()
    results = []
    
    for i, c in enumerate(cases, 1):
        t0 = time.time()
        hits = search(c["q"], k=5)
        ctx_docs = [d for _, d, _ in hits]
        recall = recall_ok(ctx_docs, c["expect"])
        
        # Get answer
        try:
            resp, used = answer(c["q"], k=5)
            passed = answer_ok(resp, c["expect"])
        except:
            resp = ""
            passed = False
            used = []
            
        dt = (time.time() - t0) * 1000
        
        results.append({
            "q": c["q"],
            "recall": recall,
            "answer_ok": passed,
            "latency_ms": round(dt, 1),
            "used": used,
        })
        
        status = "PASS" if recall else "FAIL"
        print(f"[{i:2}] {status} recall={recall} answer={passed} {round(dt,1):6.1f}ms :: {c['q'][:50]}...")
    
    # Calculate statistics
    rrate = sum(r["recall"] for r in results) / len(results)
    arate = sum(r["answer_ok"] for r in results) / len(results)
    lat = [r["latency_ms"] for r in results]
    
    summary = {
        "n": len(results),
        "recall_rate": round(rrate, 3),
        "answer_rate": round(arate, 3),
        "latency_ms_avg": round(stats.mean(lat), 1),
        "latency_ms_p95": round(stats.quantiles(lat, n=20)[18], 1) if len(lat) > 1 else max(lat),
    }
    
    # Save report
    Path("eval_unseen_report.json").write_text(
        json.dumps({"summary": summary, "results": results}, indent=2), 
        encoding="utf-8"
    )
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"  Total Queries: {summary['n']}")
    print(f"  Recall Rate: {summary['recall_rate']:.1%}")
    print(f"  Answer Rate: {summary['answer_rate']:.1%}")
    print(f"  Avg Latency: {summary['latency_ms_avg']:.1f}ms")
    print("=" * 60)
    
    # Analysis of failures
    failures = [r for r in results if not r["recall"]]
    if failures:
        print(f"\nFailed Queries ({len(failures)}):")
        for f in failures[:5]:
            print(f"  - {f['q'][:60]}...")
    
    print(f"\nThis represents a more realistic test with {len(cases)} unseen queries.")
    print("These queries were NOT used to tune the system.")


if __name__ == "__main__":
    run()