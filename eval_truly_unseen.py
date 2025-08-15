"""
Test on TRULY unseen queries - not looked at during development.
"""

import time
import json
from pathlib import Path
from search_enhancements import search
from fast_advanced_search import FastAdvancedSearch

def load_seed():
    seed_path = Path("eval_truly_unseen.jsonl")
    return [
        json.loads(line)
        for line in seed_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

def recall_ok(ctx_docs, expects):
    blob = " ".join(ctx_docs).lower()
    return all(x.lower() in blob for x in expects)

def run_truly_unseen():
    """Run evaluation on truly unseen queries"""
    print("=" * 60)
    print("TRULY UNSEEN QUERY EVALUATION")
    print("Testing queries never seen during development")
    print("=" * 60)
    
    cases = load_seed()
    
    # Test with current best system (enhanced search)
    print(f"\nTesting {len(cases)} brand new queries...")
    print("-" * 40)
    
    results = []
    latencies = []
    
    for i, c in enumerate(cases, 1):
        t0 = time.time()
        hits = search(c["q"], k=5, use_advanced=False)  # Use enhanced search
        ctx_docs = [d for _, d, _ in hits]
        recall = recall_ok(ctx_docs, c["expect"])
        dt = (time.time() - t0) * 1000
        
        results.append(recall)
        latencies.append(dt)
        
        status = "PASS" if recall else "FAIL"
        print(f"[{i:2}] {status} {dt:6.1f}ms :: {c['q'][:45]}...")
    
    # Calculate statistics
    recall_rate = sum(results) / len(results)
    avg_latency = sum(latencies) / len(latencies)
    
    print("\n" + "=" * 60)
    print("TRULY UNSEEN RESULTS:")
    print(f"  Total Queries: {len(cases)}")
    print(f"  Recall Rate: {recall_rate:.1%} ({sum(results)}/{len(results)})")
    print(f"  Avg Latency: {avg_latency:.1f}ms")
    print("=" * 60)
    
    # Show failures
    failures = [cases[i] for i, r in enumerate(results) if not r]
    if failures:
        print(f"\nFailed Queries ({len(failures)}):")
        for f in failures[:10]:
            print(f"  Q: {f['q']}")
            print(f"     Expected: {f['expect']}")
    
    # Analysis
    print("\nANALYSIS:")
    if recall_rate >= 0.9:
        print("Excellent! The system achieves 90%+ recall on truly unseen queries.")
        print("This demonstrates genuine generalization, not overfitting.")
    elif recall_rate >= 0.8:
        print("Good performance. 80%+ recall on truly unseen queries is production-ready.")
    elif recall_rate >= 0.7:
        print("Decent performance. 70%+ recall shows the system works but has room for improvement.")
    else:
        print("Performance below 70% suggests the system may have overfit to the test set.")
    
    return recall_rate

if __name__ == "__main__":
    recall = run_truly_unseen()
    print(f"\nFinal verdict: {recall:.1%} recall on genuinely unseen queries")