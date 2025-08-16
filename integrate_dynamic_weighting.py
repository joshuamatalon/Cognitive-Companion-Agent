"""
Integration of dynamic weighting into the existing hybrid RAG system.
This connects Carmelo's suggestions with our current implementation.
"""

from typing import Tuple, List, Optional
from dynamic_weighting import EnhancedHybridSearch, DynamicWeightCalculator
from hybrid_rag import HybridRAG
from production_search import ProductionAdvancedSearch

class NextGenHybridRAG(HybridRAG):
    """
    Enhanced HybridRAG with dynamic query weighting.
    Integrates Carmelo's feedback about ID/date/quote handling.
    """
    
    def __init__(self, searcher=None, llm=None):
        super().__init__(searcher, llm)
        self.enhanced_search = EnhancedHybridSearch()
        self.weight_calculator = DynamicWeightCalculator()
    
    def _search_context(self, query: str, k: int = 5) -> Tuple[List, str]:
        """
        Enhanced context search with dynamic weighting.
        Overrides parent method to use smarter search.
        """
        # Analyze query to determine best strategy
        strategy = self.weight_calculator.get_query_strategy(query)
        
        # Use enhanced search with dynamic weights
        results = self.enhanced_search.search(
            query=query,
            k=k,
            use_rrf=True  # Always use RRF as Carmelo suggested
        )
        
        # Extract documents and IDs
        doc_ids = []
        contexts = []
        
        for doc_id, text, metadata, score in results:
            doc_ids.append(doc_id)
            contexts.append(text)
        
        # Join contexts
        context = "\n\n".join(contexts)
        
        # Log the strategy used (for analytics)
        self._log_search_strategy(query, strategy)
        
        return doc_ids, context
    
    def _log_search_strategy(self, query: str, strategy: dict):
        """Log search strategy for analytics."""
        try:
            from analytics import analytics
            
            # Log as metadata
            analytics.log_query(
                query=query,
                recall_success=True,  # Will be updated later
                latency_ms=0,  # Will be updated
                results_count=len(strategy.get("ids_to_match", [])),
                source=strategy["characteristics"].query_type,
                error=None
            )
        except:
            pass  # Don't fail if analytics not available
    
    def answer(self, query: str, k: int = 5, verbose: bool = False) -> Tuple[str, List[str], str]:
        """
        Enhanced answer method with query analysis.
        """
        if verbose:
            # Show search strategy
            explanation = self.enhanced_search.explain_strategy(query)
            print(f"[Search Strategy]\n{explanation}\n")
        
        # Call parent answer method which will use our enhanced _search_context
        return super().answer(query, k, verbose)

# Update the main rag_chain.py to use enhanced version
def upgrade_rag_chain():
    """
    Upgrade rag_chain.py to use the enhanced hybrid RAG.
    This can be called to switch to the new system.
    """
    code = '''
# rag_chain.py - Enhanced version with dynamic weighting
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from memory_backend import upsert_note
from integrate_dynamic_weighting import NextGenHybridRAG
from config import config

# Check if API key is valid
if not config.is_valid():
    raise RuntimeError("Invalid configuration. Please check your API keys in .env file.")

chat_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")
llm = ChatOpenAI(model=chat_model, temperature=0, api_key=config.OPENAI_API_KEY)

# Use enhanced hybrid RAG with dynamic weighting
hybrid = NextGenHybridRAG()

def answer(query: str, k: int = 5):
    """Enhanced answer function with dynamic query weighting."""
    response, doc_ids, source = hybrid.answer(query, k)
    
    # Add source indication for transparency
    if source == "llm_knowledge":
        response += "\\n\\n[Note: Answered from AI knowledge, not from database]"
    
    # Extract and store new facts (if any) from the response
    if doc_ids:
        # Only process facts when we have context from database
        from search_enhancements import enhanced_search as search
        hits = search(query, k)
        blob = " ".join(doc for _, doc, *_ in hits).lower()
        
        for line in response.splitlines():
            if line.strip().upper().startswith("FACT:"):
                fact = line[5:].strip()
                if fact and fact.lower() not in blob:
                    upsert_note(fact, {"type": "fact", "source": "writeback"})
    
    return response, doc_ids
'''
    
    with open("rag_chain_enhanced.py", "w") as f:
        f.write(code)
    
    print("Created rag_chain_enhanced.py with dynamic weighting support")
    print("To activate: rename rag_chain_enhanced.py to rag_chain.py")

# Benchmark the improvements
def benchmark_improvements():
    """Benchmark the impact of dynamic weighting."""
    import time
    from production_search import ProductionAdvancedSearch
    
    print("=" * 60)
    print("BENCHMARKING DYNAMIC WEIGHTING IMPROVEMENTS")
    print("=" * 60)
    
    # Test queries that benefit from dynamic weighting
    test_cases = [
        {
            "query": '"cognitive AI" benefits',
            "type": "quoted phrase",
            "expected_boost": "keyword"
        },
        {
            "query": "document DOC-2024-001",
            "type": "ID lookup", 
            "expected_boost": "keyword"
        },
        {
            "query": "meetings from January 2024",
            "type": "temporal",
            "expected_boost": "balanced"
        },
        {
            "query": "8f3e2401-d0b8-4b3d-9c5e-6a2f1e3b4c5d",
            "type": "UUID lookup",
            "expected_boost": "keyword"
        },
        {
            "query": "explain vector databases",
            "type": "general",
            "expected_boost": "semantic"
        }
    ]
    
    # Initialize search systems
    old_search = ProductionAdvancedSearch()
    new_search = EnhancedHybridSearch()
    
    results = []
    
    for test in test_cases:
        print(f"\nQuery: {test['query']}")
        print(f"Type: {test['type']}")
        print(f"Expected: {test['expected_boost']} boost")
        
        # Old system
        t0 = time.time()
        old_results = old_search.search(test['query'], k=5)
        old_time = (time.time() - t0) * 1000
        
        # New system
        t0 = time.time()
        new_results = new_search.search(test['query'], k=5)
        new_time = (time.time() - t0) * 1000
        
        # Compare
        print(f"Old: {len(old_results)} results in {old_time:.1f}ms")
        print(f"New: {len(new_results)} results in {new_time:.1f}ms")
        
        # Check if results improved (would need ground truth for real comparison)
        improvement = "Unknown (need ground truth)"
        print(f"Quality: {improvement}")
        
        results.append({
            "query": test['query'],
            "old_time": old_time,
            "new_time": new_time,
            "speedup": old_time / new_time if new_time > 0 else 1.0
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    avg_old = sum(r['old_time'] for r in results) / len(results)
    avg_new = sum(r['new_time'] for r in results) / len(results)
    print(f"Average Old: {avg_old:.1f}ms")
    print(f"Average New: {avg_new:.1f}ms")
    print(f"Average Speedup: {avg_old/avg_new:.2f}x")
    print("\nDynamic weighting successfully integrated!")
    print("=" * 60)

if __name__ == "__main__":
    # Test the integration
    print("Testing NextGen Hybrid RAG with dynamic weighting...")
    
    # Create instance
    rag = NextGenHybridRAG()
    
    # Test queries
    test_queries = [
        '"exact match" for testing',
        'DOC-123 specifications',
        'January 2024 updates'
    ]
    
    for query in test_queries:
        print(f"\nProcessing: {query}")
        answer, doc_ids, source = rag.answer(query, verbose=True)
        print(f"Source: {source}")
        print(f"Found {len(doc_ids)} documents")
    
    print("\n✅ Integration successful!")
