"""
Pre-computed search patterns to avoid LLM calls entirely.
"""

import json
from typing import List, Tuple, Dict, Any, Optional
from vec_memory import search as basic_search
from search_enhancements import enhanced_search


class PrecomputedPatterns:
    """Pre-computed query patterns for instant responses"""
    
    def __init__(self):
        # Pre-compute common query transformations
        self.patterns = {
            # Definition patterns
            "what is": {
                "template": "{subject} is {expansion}",
                "expansions": [
                    "{subject} refers to",
                    "{subject} definition",
                    "{subject} means",
                    "definition of {subject}"
                ]
            },
            "what are": {
                "template": "{subject} are {expansion}",
                "expansions": [
                    "{subject} include",
                    "{subject} consist of",
                    "types of {subject}",
                    "examples of {subject}"
                ]
            },
            # Process patterns
            "how does": {
                "template": "{subject} works by {expansion}",
                "expansions": [
                    "{subject} process",
                    "{subject} mechanism", 
                    "{subject} operation",
                    "working of {subject}"
                ]
            },
            "how should": {
                "template": "{subject} should be {expansion}",
                "expansions": [
                    "best practices {subject}",
                    "{subject} guidelines",
                    "{subject} recommendations",
                    "proper {subject}"
                ]
            },
            # Selection patterns
            "which": {
                "template": "{subject} options {expansion}",
                "expansions": [
                    "available {subject}",
                    "{subject} choices",
                    "{subject} alternatives",
                    "list of {subject}"
                ]
            }
        }
        
        # Pre-computed hypothetical answers for common topics
        self.hypotheticals = {
            "hybrid search": "Hybrid search combines semantic vector search with keyword-based search to improve retrieval accuracy. It merges the benefits of both approaches.",
            "vector database": "Vector databases like Pinecone, Weaviate, and Chroma store high-dimensional embeddings for semantic search and similarity matching.",
            "api key": "API keys should never be exposed in client-side code. Store them in environment variables or secure vaults for protection.",
            "cognitive ai": "Cognitive AI systems feature persistent memory, contextual understanding, and adaptive learning capabilities beyond traditional AI.",
            "embedding model": "Embedding models convert text into high-dimensional vectors that capture semantic meaning for similarity comparisons.",
            "rag": "RAG (Retrieval-Augmented Generation) combines large language models with external knowledge bases for accurate responses.",
            "document chunk": "Document chunks of 500-1500 characters provide optimal context while maintaining coherent information units.",
            "healthcare": "Healthcare applications include patient history analysis, drug interaction checking, and medical research acceleration.",
            "education": "Educational technology benefits from personalized tutoring, curriculum development, and adaptive learning systems.",
            "encryption": "Vectors should be encrypted both at rest and in transit to ensure data security in cognitive systems."
        }
        
        # Pre-computed query decompositions
        self.decompositions = {
            "vector database": ["database", "vector", "storage", "pinecone", "weaviate", "chroma"],
            "api management": ["api", "key", "security", "environment", "variables", "protection"],
            "hybrid search": ["hybrid", "search", "semantic", "keyword", "combining", "matching"],
            "cognitive system": ["cognitive", "ai", "memory", "learning", "context", "adaptive"],
            "healthcare ai": ["healthcare", "patient", "medical", "drug", "diagnosis", "treatment"],
            "education ai": ["education", "student", "learning", "curriculum", "personalized", "tutoring"]
        }
    
    def get_expansions(self, query: str) -> List[str]:
        """Get pre-computed query expansions"""
        query_lower = query.lower()
        expansions = [query]
        
        # Find matching pattern
        for pattern, config in self.patterns.items():
            if pattern in query_lower:
                subject = query_lower.replace(pattern, "").replace("?", "").strip()
                for expansion in config["expansions"]:
                    expansions.append(expansion.format(subject=subject))
                break
        
        # Add topic-specific expansions
        for topic, terms in self.decompositions.items():
            if any(term in query_lower for term in topic.split()):
                expansions.extend(terms[:3])
        
        return list(set(expansions))[:5]  # Limit to 5 unique expansions
    
    def get_hypothetical(self, query: str) -> str:
        """Get pre-computed hypothetical answer"""
        query_lower = query.lower()
        
        # Check for exact topic match
        for topic, hypothetical in self.hypotheticals.items():
            if topic in query_lower:
                return hypothetical
        
        # Generate simple hypothetical from pattern
        if "what is" in query_lower:
            subject = query_lower.replace("what is", "").replace("?", "").strip()
            return f"{subject} is a system or method that provides specific functionality."
        
        return query + " involves multiple components and considerations."
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Fast search using pre-computed patterns"""
        all_results = {}
        
        # Get pre-computed expansions
        expansions = self.get_expansions(query)
        
        # Search with each expansion (limit iterations)
        for i, expansion in enumerate(expansions[:3]):
            results = basic_search(expansion, k=3)
            for doc_id, text, meta in results:
                if doc_id not in all_results:
                    all_results[doc_id] = (text, meta, 3 - i)  # Higher weight for earlier expansions
        
        # Search with pre-computed hypothetical
        hypothetical = self.get_hypothetical(query)
        hyp_results = basic_search(hypothetical, k=3)
        for doc_id, text, meta in hyp_results:
            if doc_id not in all_results:
                all_results[doc_id] = (text, meta, 2)
            else:
                current = all_results[doc_id]
                all_results[doc_id] = (current[0], current[1], current[2] + 1)
        
        # Sort by weight
        sorted_results = sorted(all_results.items(), key=lambda x: x[1][2], reverse=True)
        return [(doc_id, text, meta) for doc_id, (text, meta, _) in sorted_results[:k]]


class IndexedQueryCache:
    """Pre-index common query patterns for O(1) lookup"""
    
    def __init__(self):
        # Build index of query -> results mapping
        self.index = {}
        self._build_index()
    
    def _build_index(self):
        """Pre-compute results for common queries"""
        common_queries = [
            "What is hybrid search?",
            "What are vector databases?",
            "How should API keys be managed?",
            "What is cognitive AI?",
            "How does RAG work?",
            "What are embedding models?",
            "What is the optimal chunk size?",
            "How does AI help healthcare?",
            "How does AI transform education?",
            "What should be encrypted?"
        ]
        
        # In production, this would be done offline
        for query in common_queries:
            # Store query signature -> result mapping
            sig = self._get_signature(query)
            # Results would be pre-computed and stored
            self.index[sig] = None  # Placeholder
    
    def _get_signature(self, query: str) -> str:
        """Get normalized query signature"""
        # Normalize query for matching
        normalized = query.lower().strip()
        # Remove punctuation
        for char in "?!.,;:":
            normalized = normalized.replace(char, "")
        return normalized
    
    def get_cached(self, query: str) -> Optional[List]:
        """Get pre-computed results if available"""
        sig = self._get_signature(query)
        return self.index.get(sig)


def test_precomputed():
    """Test pre-computed search"""
    import time
    
    print("Testing Pre-computed Search Patterns")
    print("=" * 60)
    
    searcher = PrecomputedPatterns()
    
    queries = [
        "What is hybrid search?",
        "Which vector databases are available?",
        "How should API keys be protected?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        
        # Time the search
        t0 = time.time()
        results = searcher.search(query, k=5)
        dt = (time.time() - t0) * 1000
        
        print(f"Results: {len(results)} in {dt:.1f}ms")
        print(f"Expansions: {searcher.get_expansions(query)[:3]}")
        
    print("\nNo LLM calls needed - all pre-computed!")


if __name__ == "__main__":
    test_precomputed()