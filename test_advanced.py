"""
Quick test of advanced search on failing queries.
"""

from advanced_search import UnifiedAdvancedSearch
import time

def test_failing_queries():
    """Test queries that were failing"""
    
    print("Testing Advanced Search on Previously Failing Queries")
    print("=" * 60)
    
    searcher = UnifiedAdvancedSearch()
    
    # The queries that were failing
    test_cases = [
        {
            "q": "What is hybrid search?",
            "expect": ["semantic", "keyword", "combining"]
        },
        {
            "q": "Which vector databases are mentioned for cognitive AI?",
            "expect": ["pinecone", "weaviate", "chroma"]
        },
        {
            "q": "How should API keys be managed?",
            "expect": ["never expose", "environment", "secure"]
        },
        {
            "q": "What benefits does healthcare see from cognitive AI?",
            "expect": ["patient", "drug", "research"]
        },
        {
            "q": "How does cognitive AI transform education?",
            "expect": ["personalized", "curriculum", "learning"]
        }
    ]
    
    results_summary = []
    
    for case in test_cases:
        query = case["q"]
        expected = case["expect"]
        
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        # Test unified search
        t0 = time.time()
        results = searcher.search(query, k=5, method='all')
        dt = (time.time() - t0) * 1000
        
        # Check if expected terms are found
        combined_text = " ".join([r[1] for r in results]).lower()
        found = all(term.lower() in combined_text for term in expected)
        
        status = "PASS" if found else "FAIL"
        results_summary.append(found)
        
        print(f"Status: {status}")
        print(f"Latency: {dt:.1f}ms")
        print(f"Found {len(results)} results")
        
        if not found:
            missing = [term for term in expected if term.lower() not in combined_text]
            print(f"Missing terms: {missing}")
            print(f"First result: {results[0][1][:150]}..." if results else "No results")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    recall_rate = sum(results_summary) / len(results_summary)
    print(f"Recall: {len([r for r in results_summary if r])}/{len(results_summary)} = {recall_rate:.1%}")
    
    if recall_rate >= 0.8:
        print("Advanced search shows significant improvement!")
    else:
        print("Advanced search needs more tuning.")
    
    return recall_rate


if __name__ == "__main__":
    recall = test_failing_queries()
    print(f"\nFinal recall on hard queries: {recall:.1%}")