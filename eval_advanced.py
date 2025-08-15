"""
Evaluate advanced search methods on unseen queries.
"""

import time
import json
from pathlib import Path
from search_enhancements import search
from fast_advanced_search import FastAdvancedSearch

def load_seed():
    seed_path = Path("eval_seed_unseen.jsonl")
    if not seed_path.exists():
        raise SystemExit(f"Create {seed_path}")
    return [
        json.loads(line)
        for line in seed_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

def recall_ok(ctx_docs, expects):
    blob = " ".join(ctx_docs).lower()
    return all(x.lower() in blob for x in expects)

def compare_methods():
    """Compare enhanced vs advanced search"""
    print("=" * 60)
    print("COMPARING SEARCH METHODS ON UNSEEN QUERIES")
    print("=" * 60)
    
    cases = load_seed()
    
    # Test enhanced search
    print("\n1. ENHANCED SEARCH (current production)")
    print("-" * 40)
    enhanced_results = []
    
    for i, c in enumerate(cases, 1):
        t0 = time.time()
        hits = search(c["q"], k=5, use_advanced=False)
        ctx_docs = [d for _, d, _ in hits]
        recall = recall_ok(ctx_docs, c["expect"])
        dt = (time.time() - t0) * 1000
        
        enhanced_results.append(recall)
        status = "PASS" if recall else "FAIL"
        print(f"[{i:2}] {status} {dt:6.1f}ms :: {c['q'][:40]}...")
    
    enhanced_recall = sum(enhanced_results) / len(enhanced_results)
    print(f"\nEnhanced Recall: {enhanced_recall:.1%}")
    
    # Test advanced search
    print("\n2. ADVANCED SEARCH (with 4 novel methods)")
    print("-" * 40)
    advanced_results = []
    
    searcher = FastAdvancedSearch()
    
    for i, c in enumerate(cases, 1):
        t0 = time.time()
        hits = searcher.search(c["q"], k=5)
        ctx_docs = [d for _, d, _ in hits]
        recall = recall_ok(ctx_docs, c["expect"])
        dt = (time.time() - t0) * 1000
        
        advanced_results.append(recall)
        status = "PASS" if recall else "FAIL"
        print(f"[{i:2}] {status} {dt:6.1f}ms :: {c['q'][:40]}...")
    
    advanced_recall = sum(advanced_results) / len(advanced_results)
    print(f"\nAdvanced Recall: {advanced_recall:.1%}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"Enhanced Search: {enhanced_recall:.1%} recall")
    print(f"Advanced Search: {advanced_recall:.1%} recall")
    
    improvement = (advanced_recall - enhanced_recall) * 100
    if improvement > 0:
        print(f"Improvement: +{improvement:.1f} percentage points")
    else:
        print(f"Change: {improvement:.1f} percentage points")
    
    # Show which queries improved
    print("\nQueries that improved with advanced search:")
    for i, c in enumerate(cases):
        if advanced_results[i] and not enhanced_results[i]:
            print(f"  - {c['q']}")
    
    print("\nQueries that got worse with advanced search:")
    for i, c in enumerate(cases):
        if enhanced_results[i] and not advanced_results[i]:
            print(f"  - {c['q']}")

if __name__ == "__main__":
    compare_methods()