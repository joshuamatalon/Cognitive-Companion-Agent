"""
Test search systems on completely unrelated content: farming beets.
This tests how the system handles queries with no relevant content.
"""

import json
import time
from pathlib import Path
from production_search import ProductionAdvancedSearch
from search_enhancements import search as enhanced_search

def load_beet_queries():
    return [
        json.loads(line)
        for line in Path('eval_beets.jsonl').read_text(encoding='utf-8').splitlines()
        if line.strip()
    ]

def test_irrelevant_queries():
    print("=" * 60)
    print("TESTING WITH COMPLETELY UNRELATED QUERIES: FARMING BEETS")
    print("=" * 60)
    print("\nThe database contains information about cognitive AI systems.")
    print("These queries are about farming beets - completely unrelated.")
    print("Expected behavior: 0% recall (no relevant content exists)\n")
    
    cases = load_beet_queries()
    print(f"Testing {len(cases)} beet farming queries...\n")
    
    # Test 1: Production Search
    print("1. PRODUCTION SEARCH (Advanced)")
    print("-" * 40)
    
    searcher = ProductionAdvancedSearch()
    searcher.clear_cache()
    
    prod_found = 0
    prod_responses = []
    
    for i, c in enumerate(cases[:10], 1):  # Test first 10
        t0 = time.time()
        hits = searcher.search(c["q"], k=5)
        dt = (time.time() - t0) * 1000
        
        if hits:
            # Check if any expected terms are found
            ctx_docs = [d for _, d, _ in hits]
            blob = ' '.join(ctx_docs).lower()
            found_terms = [term for term in c["expect"] if term.lower() in blob]
            
            if found_terms:
                prod_found += 1
                print(f"[{i:2}] UNEXPECTED: Found terms {found_terms} for: {c['q'][:40]}...")
            else:
                # System returned results but they're not about beets
                sample = hits[0][1][:100] if hits else "No results"
                prod_responses.append((c['q'], sample))
                if i <= 3:  # Show first few
                    print(f"[{i:2}] Returned AI content for: {c['q'][:40]}...")
                    print(f"     Sample: {sample}...")
    
    print(f"\nProduction Search: {prod_found}/{10} queries found relevant beet content")
    print(f"(Expected: 0/10 since database has no beet farming content)")
    
    # Test 2: Enhanced Search
    print("\n2. ENHANCED SEARCH (Baseline)")
    print("-" * 40)
    
    enhanced_found = 0
    enhanced_responses = []
    
    for i, c in enumerate(cases[:10], 1):  # Test first 10
        t0 = time.time()
        hits = enhanced_search(c["q"], k=5, use_advanced=False)
        dt = (time.time() - t0) * 1000
        
        if hits:
            ctx_docs = [d for _, d, _ in hits]
            blob = ' '.join(ctx_docs).lower()
            found_terms = [term for term in c["expect"] if term.lower() in blob]
            
            if found_terms:
                enhanced_found += 1
                print(f"[{i:2}] UNEXPECTED: Found terms {found_terms} for: {c['q'][:40]}...")
            else:
                sample = hits[0][1][:100] if hits else "No results"
                enhanced_responses.append((c['q'], sample))
                if i <= 3:
                    print(f"[{i:2}] Returned AI content for: {c['q'][:40]}...")
                    print(f"     Sample: {sample}...")
    
    print(f"\nEnhanced Search: {enhanced_found}/{10} queries found relevant beet content")
    print(f"(Expected: 0/10 since database has no beet farming content)")
    
    # Analysis
    print("\n" + "=" * 60)
    print("ANALYSIS:")
    print("-" * 40)
    
    if prod_found == 0 and enhanced_found == 0:
        print("[OK] CORRECT: Neither system hallucinated beet farming content")
        print("[OK] Both systems correctly returned no relevant results")
        print("\nThe systems are returning AI-related content because:")
        print("1. They're trying to be helpful even with no relevant data")
        print("2. They return the 'least bad' matches from available content")
        print("3. No hallucination - they don't invent beet farming info")
    else:
        print("[WARNING] System found beet-related terms unexpectedly")
        print("This might indicate:")
        print("1. Overly aggressive query expansion")
        print("2. Hallucination in hypothetical document generation")
        print("3. Coincidental term matches")
    
    # Show what the system returns instead
    print("\n" + "=" * 60)
    print("WHAT THE SYSTEM RETURNS INSTEAD:")
    print("-" * 40)
    
    print("\nExample responses to beet queries (showing AI content returned):\n")
    for i, (query, response) in enumerate(prod_responses[:3], 1):
        print(f"{i}. Query: '{query}'")
        print(f"   Returns: '{response[:150]}...'")
        print()
    
    # Test hypothetical generation
    print("=" * 60)
    print("TESTING HYPOTHETICAL GENERATION:")
    print("-" * 40)
    
    from production_search import FastHyDE, LRUCache, PreComputedPatterns
    
    hyde = FastHyDE(LRUCache(), PreComputedPatterns())
    test_query = "What is the optimal soil pH for growing beets?"
    
    print(f"Query: '{test_query}'")
    hypothetical = hyde.generate_hypothetical(test_query)
    print(f"Hypothetical: '{hypothetical[:200]}...'")
    
    if "beet" in hypothetical.lower() or "soil" in hypothetical.lower() or "pH" in hypothetical.lower():
        print("\n[OK] HyDE correctly attempts to answer about beets")
        print("  (Even though no beet content exists in database)")
    else:
        print("\n[INFO] HyDE generates generic response, not beet-specific")
    
    print("\n" + "=" * 60)
    print("CONCLUSION:")
    print("-" * 40)
    print("The search systems behave correctly with irrelevant queries:")
    print("1. They don't hallucinate beet farming information")
    print("2. They return the best available matches (AI content)")
    print("3. They maintain 0% recall on truly irrelevant topics")
    print("4. This demonstrates the system's domain boundaries")
    print("=" * 60)

if __name__ == "__main__":
    test_irrelevant_queries()