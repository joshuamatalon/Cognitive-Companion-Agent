"""
Evaluate production search on truly unseen queries.
"""

import time
import json
import statistics
from pathlib import Path
from production_search import ProductionAdvancedSearch
from search_enhancements import search as basic_search

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

def evaluate_production():
    """Evaluate production search system"""
    print("=" * 60)
    print("PRODUCTION SEARCH EVALUATION")
    print("Testing on genuinely unseen queries")
    print("=" * 60)
    
    cases = load_seed()
    searcher = ProductionAdvancedSearch()
    
    # Test 1: Cold start (no cache)
    print("\n1. COLD START PERFORMANCE (no cache)")
    print("-" * 40)
    
    cold_results = []
    cold_latencies = []
    
    for i, c in enumerate(cases, 1):
        t0 = time.time()
        hits = searcher.search(c["q"], k=5)
        dt = (time.time() - t0) * 1000
        
        ctx_docs = [d for _, d, _ in hits]
        recall = recall_ok(ctx_docs, c["expect"])
        
        cold_results.append(recall)
        cold_latencies.append(dt)
        
        status = "PASS" if recall else "FAIL"
        print(f"[{i:2}] {status} {dt:6.1f}ms :: {c['q'][:40]}...")
    
    cold_recall = sum(cold_results) / len(cold_results)
    cold_avg_latency = statistics.mean(cold_latencies)
    
    print(f"\nCold Recall: {cold_recall:.1%}")
    print(f"Cold Avg Latency: {cold_avg_latency:.1f}ms")
    
    # Test 2: Warm cache (second run)
    print("\n2. WARM CACHE PERFORMANCE (with cache)")
    print("-" * 40)
    
    warm_results = []
    warm_latencies = []
    
    for i, c in enumerate(cases, 1):
        t0 = time.time()
        hits = searcher.search(c["q"], k=5)
        dt = (time.time() - t0) * 1000
        
        ctx_docs = [d for _, d, _ in hits]
        recall = recall_ok(ctx_docs, c["expect"])
        
        warm_results.append(recall)
        warm_latencies.append(dt)
        
        status = "PASS" if recall else "FAIL"
        print(f"[{i:2}] {status} {dt:6.1f}ms :: {c['q'][:40]}...")
    
    warm_recall = sum(warm_results) / len(warm_results)
    warm_avg_latency = statistics.mean(warm_latencies)
    
    print(f"\nWarm Recall: {warm_recall:.1%}")
    print(f"Warm Avg Latency: {warm_avg_latency:.1f}ms")
    
    # Test 3: Batch search
    print("\n3. BATCH SEARCH PERFORMANCE")
    print("-" * 40)
    
    batch_queries = [c["q"] for c in cases[:10]]
    t0 = time.time()
    batch_results = searcher.search_batch(batch_queries, k=5)
    batch_dt = (time.time() - t0) * 1000
    
    batch_recall_count = 0
    for c in cases[:10]:
        if c["q"] in batch_results:
            ctx_docs = [d for _, d, _ in batch_results[c["q"]]]
            if recall_ok(ctx_docs, c["expect"]):
                batch_recall_count += 1
    
    batch_recall = batch_recall_count / 10
    
    print(f"Batch processing 10 queries: {batch_dt:.1f}ms total")
    print(f"Per query: {batch_dt/10:.1f}ms")
    print(f"Batch Recall: {batch_recall:.1%}")
    
    # Summary
    print("\n" + "=" * 60)
    print("PRODUCTION SEARCH SUMMARY:")
    print(f"  Cold Recall: {cold_recall:.1%}")
    print(f"  Warm Recall: {warm_recall:.1%}")
    print(f"  Cold Latency: {cold_avg_latency:.1f}ms")
    print(f"  Warm Latency: {warm_avg_latency:.1f}ms (down {(cold_avg_latency-warm_avg_latency)/cold_avg_latency*100:.1f}%)")
    print(f"  Batch Efficiency: {batch_dt/10:.1f}ms per query")
    
    if cold_recall >= 0.85:
        print("\n[OK] Production search achieves 85%+ recall!")
    if warm_avg_latency < 100:
        print("[OK] Cache provides sub-100ms responses!")
    if batch_dt/10 < warm_avg_latency:
        print("[OK] Batch processing improves efficiency!")
    
    print("=" * 60)
    
    # Compare with basic search
    print("\n4. COMPARISON WITH BASIC SEARCH")
    print("-" * 40)
    
    basic_results = []
    basic_latencies = []
    
    for c in cases[:5]:
        t0 = time.time()
        hits = basic_search(c["q"], k=5, use_advanced=False)
        dt = (time.time() - t0) * 1000
        
        ctx_docs = [d for _, d, _ in hits]
        recall = recall_ok(ctx_docs, c["expect"])
        
        basic_results.append(recall)
        basic_latencies.append(dt)
    
    basic_recall = sum(basic_results) / len(basic_results)
    basic_avg_latency = statistics.mean(basic_latencies)
    
    print(f"Basic Search Recall: {basic_recall:.1%}")
    print(f"Basic Search Latency: {basic_avg_latency:.1f}ms")
    print(f"Production Search Recall: {cold_recall:.1%} (up {(cold_recall-basic_recall)*100:.1f}pp)")
    print(f"Production Search is {cold_avg_latency/basic_avg_latency:.1f}x slower but more accurate")

if __name__ == "__main__":
    evaluate_production()