"""
Test hybrid search implementation with cases that need exact matching.
"""

import json
from pathlib import Path
from search_enhancements import search, hybrid_search, enhanced_search
from keyword_search import get_keyword_index


def test_exact_match_cases():
    """Test cases that should improve with hybrid search."""
    
    test_cases = [
        # Exact ID/code matches
        {
            "query": "Find document with ID ABC-123",
            "expected_terms": ["ABC-123"],
            "description": "Exact ID match"
        },
        
        # Dollar amounts
        {
            "query": "What is the $2,100 payment?",
            "expected_terms": ["2100", "$2,100", "payment"],
            "description": "Dollar amount search"
        },
        {
            "query": "Show me the $2100 expense",
            "expected_terms": ["2100", "$2100", "expense"],
            "description": "Dollar amount without comma"
        },
        
        # Specific numbers
        {
            "query": "18-24 month objective",
            "expected_terms": ["18-24", "month", "objective"],
            "description": "Date range"
        },
        {
            "query": "What is 91.7% recall?",
            "expected_terms": ["91.7", "recall"],
            "description": "Percentage search"
        },
        
        # Proper nouns
        {
            "query": "LangChain documentation",
            "expected_terms": ["LangChain"],
            "description": "Proper noun search"
        },
        {
            "query": "Pinecone vector database",
            "expected_terms": ["Pinecone", "vector"],
            "description": "Technical terms"
        },
    ]
    
    print("=" * 60)
    print("Testing Hybrid Search with Exact Match Cases")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Query: {test_case['query']}")
        print(f"Expected terms: {test_case['expected_terms']}")
        
        # Test with hybrid search (default)
        try:
            hybrid_results = search(test_case['query'], k=5, use_hybrid=True)
            print(f"Hybrid results: {len(hybrid_results)} documents found")
            
            # Check if expected terms are in results
            found_terms = []
            for _, text, _ in hybrid_results[:3]:  # Check top 3 results
                text_lower = text.lower()
                for term in test_case['expected_terms']:
                    if term.lower() in text_lower:
                        found_terms.append(term)
            
            if found_terms:
                print(f"✓ Found terms: {list(set(found_terms))}")
            else:
                print(f"✗ No expected terms found in top results")
                
        except Exception as e:
            print(f"Error in hybrid search: {e}")
        
        # Compare with pure vector search
        try:
            vector_results = search(test_case['query'], k=5, use_hybrid=False)
            print(f"Vector-only results: {len(vector_results)} documents found")
        except Exception as e:
            print(f"Error in vector search: {e}")
    
    print("\n" + "=" * 60)


def test_alpha_tuning():
    """Test different alpha values to find optimal balance."""
    
    test_query = "What is my 18-24 month objective?"
    alpha_values = [0.5, 0.6, 0.7, 0.8, 0.9]
    
    print("\n" + "=" * 60)
    print("Testing Alpha Parameter Tuning")
    print("=" * 60)
    print(f"Query: {test_query}")
    
    for alpha in alpha_values:
        print(f"\nAlpha = {alpha} (Vector: {alpha*100:.0f}%, Keyword: {(1-alpha)*100:.0f}%)")
        
        try:
            results = hybrid_search(test_query, k=5, alpha=alpha)
            print(f"Results: {len(results)} documents")
            
            # Show top result snippet
            if results:
                doc_id, text, _, score = results[0]
                snippet = text[:100] + "..." if len(text) > 100 else text
                print(f"Top result (score={score:.3f}): {snippet}")
                
        except Exception as e:
            print(f"Error with alpha={alpha}: {e}")
    
    print("\n" + "=" * 60)


def test_rrf_vs_weighted():
    """Compare Reciprocal Rank Fusion vs Weighted Average."""
    
    test_query = "What helps with AI security?"
    
    print("\n" + "=" * 60)
    print("Testing RRF vs Weighted Average")
    print("=" * 60)
    print(f"Query: {test_query}")
    
    # Test weighted average
    print("\n--- Weighted Average (alpha=0.7) ---")
    try:
        weighted_results = hybrid_search(test_query, k=5, alpha=0.7, use_rrf=False)
        print(f"Results: {len(weighted_results)} documents")
        for i, (doc_id, text, _, score) in enumerate(weighted_results[:3], 1):
            snippet = text[:80] + "..." if len(text) > 80 else text
            print(f"{i}. (score={score:.3f}) {snippet}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test RRF
    print("\n--- Reciprocal Rank Fusion ---")
    try:
        rrf_results = hybrid_search(test_query, k=5, alpha=0.7, use_rrf=True)
        print(f"Results: {len(rrf_results)} documents")
        for i, (doc_id, text, _, score) in enumerate(rrf_results[:3], 1):
            snippet = text[:80] + "..." if len(text) > 80 else text
            print(f"{i}. (RRF score={score:.4f}) {snippet}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)


def check_keyword_index_status():
    """Check the status of the keyword index."""
    
    print("\n" + "=" * 60)
    print("Keyword Index Status")
    print("=" * 60)
    
    try:
        keyword_index = get_keyword_index()
        stats = keyword_index.get_stats()
        
        print(f"Total documents: {stats['total_documents']}")
        print(f"Index type: {stats['index_type']}")
        print(f"Storage: {stats['storage']}")
        print(f"Database: {stats['db_path']}")
        
        # Test a simple keyword search
        test_results = keyword_index.search("objective", k=3)
        print(f"\nTest search for 'objective': {len(test_results)} results")
        
    except Exception as e:
        print(f"Error checking keyword index: {e}")
    
    print("=" * 60)


if __name__ == "__main__":
    print("\nStarting Hybrid Search Tests\n")
    
    # Check keyword index status first
    check_keyword_index_status()
    
    # Run test suites
    test_exact_match_cases()
    test_alpha_tuning()
    test_rrf_vs_weighted()
    
    print("\nAll tests completed!\n")