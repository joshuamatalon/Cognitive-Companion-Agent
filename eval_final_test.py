"""
Final genuine unseen test of production search system.
These queries have never been seen during development.
"""

import time
import json
import statistics
from pathlib import Path
from production_search import ProductionAdvancedSearch
from search_enhancements import search as enhanced_search

def load_seed():
    seed_path = Path("eval_final_unseen.jsonl")
    return [
        json.loads(line)
        for line in seed_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

def recall_ok(ctx_docs, expects):
    blob = " ".join(ctx_docs).lower()
    return all(x.lower() in blob for x in expects)

def run_final_test():
    """Run final unseen evaluation"""
    print("=" * 60)
    print("FINAL GENUINE UNSEEN TEST")
    print("25 brand new queries never used in development")
    print("=" * 60)
    
    cases = load_seed()
    print(f"\nLoaded {len(cases)} genuinely unseen test queries")
    
    # Initialize search systems
    production_searcher = ProductionAdvancedSearch()
    production_searcher.clear_cache()  # Ensure no cache advantage
    print("Cache cleared for fair testing\n")
    
    # Test 1: Production Search (Advanced)
    print("1. PRODUCTION SEARCH (with all optimizations)")
    print("-" * 40)
    
    prod_results = []
    prod_latencies = []
    prod_failures = []
    
    for i, c in enumerate(cases, 1):
        t0 = time.time()
        hits = production_searcher.search(c["q"], k=5)
        dt = (time.time() - t0) * 1000
        
        ctx_docs = [d for _, d, _ in hits]
        recall = recall_ok(ctx_docs, c["expect"])
        
        prod_results.append(recall)
        prod_latencies.append(dt)
        
        status = "PASS" if recall else "FAIL"
        if not recall:
            prod_failures.append(c)
        
        # Show progress for every 5th query
        if i % 5 == 0 or not recall:
            print(f"[{i:2}] {status} {dt:6.1f}ms :: {c['q'][:45]}...")
    
    prod_recall = sum(prod_results) / len(prod_results)
    prod_avg_latency = statistics.mean(prod_latencies)
    prod_median_latency = statistics.median(prod_latencies)
    
    print(f"\nProduction Recall: {prod_recall:.1%} ({sum(prod_results)}/{len(prod_results)})")
    print(f"Production Avg Latency: {prod_avg_latency:.1f}ms")
    print(f"Production Median Latency: {prod_median_latency:.1f}ms")
    
    # Test 2: Enhanced Search (Baseline)
    print("\n2. ENHANCED SEARCH (baseline without advanced methods)")
    print("-" * 40)
    
    enhanced_results = []
    enhanced_latencies = []
    enhanced_failures = []
    
    for i, c in enumerate(cases, 1):
        t0 = time.time()
        hits = enhanced_search(c["q"], k=5, use_advanced=False)
        dt = (time.time() - t0) * 1000
        
        ctx_docs = [d for _, d, _ in hits]
        recall = recall_ok(ctx_docs, c["expect"])
        
        enhanced_results.append(recall)
        enhanced_latencies.append(dt)
        
        status = "PASS" if recall else "FAIL"
        if not recall:
            enhanced_failures.append(c)
        
        # Show progress for every 5th query
        if i % 5 == 0 or not recall:
            print(f"[{i:2}] {status} {dt:6.1f}ms :: {c['q'][:45]}...")
    
    enhanced_recall = sum(enhanced_results) / len(enhanced_results)
    enhanced_avg_latency = statistics.mean(enhanced_latencies)
    enhanced_median_latency = statistics.median(enhanced_latencies)
    
    print(f"\nEnhanced Recall: {enhanced_recall:.1%} ({sum(enhanced_results)}/{len(enhanced_results)})")
    print(f"Enhanced Avg Latency: {enhanced_avg_latency:.1f}ms")
    print(f"Enhanced Median Latency: {enhanced_median_latency:.1f}ms")
    
    # Comparison
    print("\n" + "=" * 60)
    print("FINAL RESULTS COMPARISON:")
    print("-" * 40)
    print(f"Production Search: {prod_recall:.1%} recall, {prod_avg_latency:.0f}ms avg")
    print(f"Enhanced Search:   {enhanced_recall:.1%} recall, {enhanced_avg_latency:.0f}ms avg")
    
    recall_improvement = (prod_recall - enhanced_recall) * 100
    if recall_improvement > 0:
        print(f"\nProduction search improves recall by {recall_improvement:.1f} percentage points")
    elif recall_improvement < 0:
        print(f"\nProduction search decreases recall by {abs(recall_improvement):.1f} percentage points")
    else:
        print(f"\nBoth systems achieve equal recall")
    
    latency_ratio = prod_avg_latency / enhanced_avg_latency
    print(f"Production search is {latency_ratio:.1f}x slower but ", end="")
    if prod_recall > enhanced_recall:
        print("more accurate")
    elif prod_recall < enhanced_recall:
        print("less accurate (unexpected)")
    else:
        print("equally accurate")
    
    # Show specific improvements
    print("\n" + "=" * 60)
    print("DETAILED ANALYSIS:")
    print("-" * 40)
    
    # Queries that only production got right
    prod_only = []
    enhanced_only = []
    both_failed = []
    
    for i, c in enumerate(cases):
        if prod_results[i] and not enhanced_results[i]:
            prod_only.append(c["q"])
        elif enhanced_results[i] and not prod_results[i]:
            enhanced_only.append(c["q"])
        elif not prod_results[i] and not enhanced_results[i]:
            both_failed.append(c["q"])
    
    if prod_only:
        print(f"\nQueries only Production got right ({len(prod_only)}):")
        for q in prod_only[:5]:
            print(f"  - {q}")
    
    if enhanced_only:
        print(f"\nQueries only Enhanced got right ({len(enhanced_only)}):")
        for q in enhanced_only[:5]:
            print(f"  - {q}")
    
    if both_failed:
        print(f"\nQueries both systems failed ({len(both_failed)}):")
        for q in both_failed[:5]:
            print(f"  - {q}")
    
    # Final verdict
    print("\n" + "=" * 60)
    print("FINAL VERDICT:")
    print("-" * 40)
    
    if prod_recall >= 0.85:
        print("[PASS] Production search achieves 85%+ recall on genuinely unseen queries")
    else:
        print(f"[INFO] Production search achieves {prod_recall:.1%} recall")
    
    if prod_avg_latency < 5000:
        print("[PASS] Production search responds within 5 seconds")
    else:
        print(f"[INFO] Production search takes {prod_avg_latency:.0f}ms average")
    
    if prod_recall > enhanced_recall:
        print(f"[PASS] Production search improves recall by {recall_improvement:.1f}pp over baseline")
    elif prod_recall == enhanced_recall:
        print("[INFO] Production search matches baseline recall")
    else:
        print(f"[WARN] Production search underperforms baseline by {abs(recall_improvement):.1f}pp")
    
    print("\nThis represents a genuine test on completely unseen data.")
    print("=" * 60)
    
    return prod_recall, enhanced_recall

if __name__ == "__main__":
    prod_recall, enhanced_recall = run_final_test()
    print(f"\nFinal scores: Production {prod_recall:.1%} vs Enhanced {enhanced_recall:.1%}")