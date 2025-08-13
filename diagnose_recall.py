"""Diagnostic tool to understand recall issues and provide recommendations."""
import json
from pathlib import Path
from vec_memory import search as basic_search
from search_enhancements import enhanced_search, extract_key_terms, extract_patterns
import time

def load_eval_seed():
    """Load evaluation seed cases."""
    seed_path = Path("eval_seed.jsonl")
    if not seed_path.exists():
        print("ERROR: eval_seed.jsonl not found")
        return []
    
    cases = []
    for line in seed_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


def diagnose_search(query: str, expected: list):
    """Diagnose search performance for a query."""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"Expected terms: {expected}")
    print(f"{'='*60}")
    
    # Try basic search
    print("\n1. BASIC SEARCH:")
    t0 = time.time()
    basic_results = basic_search(query, k=5)
    basic_time = (time.time() - t0) * 1000
    print(f"   Time: {basic_time:.1f}ms")
    print(f"   Results found: {len(basic_results)}")
    
    if basic_results:
        for i, (id_, text, meta) in enumerate(basic_results[:2], 1):
            print(f"   Result {i}:")
            print(f"     ID: {id_}")
            print(f"     Text preview: {text[:100] if text else 'None'}")
            print(f"     Metadata: {meta}")
    
    # Check if expected terms found
    if basic_results:
        all_text = " ".join([r[1] or "" for r in basic_results]).lower()
        found = [e for e in expected if e.lower() in all_text]
        missing = [e for e in expected if e.lower() not in all_text]
        print(f"   Found terms: {found}")
        print(f"   Missing terms: {missing}")
    else:
        print(f"   ERROR: No results found")
    
    # Try enhanced search
    print("\n2. ENHANCED SEARCH:")
    t0 = time.time()
    enhanced_results = enhanced_search(query, k=5)
    enhanced_time = (time.time() - t0) * 1000
    print(f"   Time: {enhanced_time:.1f}ms")
    print(f"   Results found: {len(enhanced_results)}")
    
    if enhanced_results:
        for i, (id_, text, meta) in enumerate(enhanced_results[:2], 1):
            print(f"   Result {i}:")
            print(f"     ID: {id_}")
            print(f"     Text preview: {text[:100] if text else 'None'}")
            print(f"     Metadata: {meta}")
    
    # Check if expected terms found
    if enhanced_results:
        all_text = " ".join([r[1] or "" for r in enhanced_results]).lower()
        found = [e for e in expected if e.lower() in all_text]
        missing = [e for e in expected if e.lower() not in all_text]
        print(f"   Found terms: {found}")
        print(f"   Missing terms: {missing}")
    else:
        print(f"   ERROR: No results found")
    
    # Show search strategies
    print("\n3. SEARCH STRATEGIES APPLIED:")
    print(f"   Key terms: {extract_key_terms(query)}")
    print(f"   Patterns: {extract_patterns(query)}")
    
    return len(enhanced_results) > 0 and all(e.lower() in all_text for e in expected)


def check_database_content():
    """Check what's actually in the database."""
    print("\n" + "="*60)
    print("DATABASE CONTENT CHECK")
    print("="*60)
    
    # Try various test queries
    test_queries = [
        "Josh",
        "equity",
        "AI",
        "frontier",
        "2100",
        "128000",
        "LangChain",
        "Pinecone",
        "Phase 1",
        "objective",
        "student loan"
    ]
    
    found_content = False
    for q in test_queries:
        results = basic_search(q, k=1)
        if results and results[0][1] and results[0][1] != "None":
            print(f"[OK] Found content for '{q}': {results[0][1][:50]}...")
            found_content = True
        else:
            print(f"[X] No valid content for '{q}'")
    
    return found_content


def main():
    """Run diagnostic on recall issues."""
    print("COGNITIVE COMPANION RECALL DIAGNOSTIC")
    print("=" * 60)
    
    # Check database content first
    has_content = check_database_content()
    
    if not has_content:
        print("\nWARNING: Database appears to have no valid content!")
        print("   The text field in all vectors is 'None' or empty.")
        print("\nRECOMMENDATIONS:")
        print("   1. Re-ingest your PDF documents")
        print("   2. Check that ingestors.py is properly saving text content")
        print("   3. Verify vec_memory.upsert_note is receiving text data")
        return
    
    # Load and test eval cases
    cases = load_eval_seed()
    if not cases:
        print("\nNo evaluation cases found")
        return
    
    print(f"\nTesting {len(cases)} evaluation cases...")
    
    passed = 0
    failed = 0
    
    for case in cases:
        if diagnose_search(case["q"], case["expect"]):
            passed += 1
        else:
            failed += 1
    
    # Summary and recommendations
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Passed: {passed}/{len(cases)}")
    print(f"Failed: {failed}/{len(cases)}")
    print(f"Recall rate: {passed/len(cases)*100:.1f}%")
    
    print("\n📋 RECOMMENDATIONS:")
    if failed > 0:
        print("   1. Check if the expected content is actually in the database")
        print("   2. Re-ingest documents with better chunking strategy")
        print("   3. Add more synonym mappings for domain-specific terms")
        print("   4. Consider adjusting the embedding model or search parameters")
    else:
        print("   Search is working well!")


if __name__ == "__main__":
    main()