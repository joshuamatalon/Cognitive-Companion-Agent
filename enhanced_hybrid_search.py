"""
Enhanced hybrid search implementing Carmelo's suggestions:
1. Better RRF (Reciprocal Rank Fusion) with score normalization
2. Dynamic weighting based on query characteristics
3. Cross-encoder optimization for semantic ordering
"""

import re
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
import hashlib
from collections import defaultdict

from vec_memory import search as basic_search
from keyword_search import get_keyword_index
from search_enhancements import enhanced_search

# Try to import cross-encoder
try:
    from sentence_transformers import CrossEncoder
    HAS_CROSS_ENCODER = True
except ImportError:
    HAS_CROSS_ENCODER = False

@dataclass
class QueryCharacteristics:
    """Analyze query to determine optimal search strategy."""
    has_quotes: bool = False
    has_dates: bool = False
    has_ids: bool = False
    has_numbers: bool = False
    exact_phrases: List[str] = None
    query_type: str = "semantic"  # semantic, exact, hybrid
    
    def __post_init__(self):
        if self.exact_phrases is None:
            self.exact_phrases = []

class DynamicHybridSearch:
    """
    Hybrid search with dynamic weighting based on query characteristics.
    Implements Carmelo's suggestions for better recall and precision.
    """
    
    def __init__(self):
        self.cross_encoder = None
        if HAS_CROSS_ENCODER:
            try:
                # Use a better cross-encoder model
                self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
                print("✅ Cross-encoder loaded for semantic reordering")
            except:
                print("⚠️ Cross-encoder not available, using fallback")
        
        self.keyword_index = get_keyword_index()
    
    def analyze_query(self, query: str) -> QueryCharacteristics:
        """
        Analyze query characteristics to determine search strategy.
        Based on Carmelo's suggestion for dynamic weighting.
        """
        chars = QueryCharacteristics()
        
        # Check for quoted phrases (exact match needed)
        quote_pattern = r'"([^"]*)"'
        quoted_matches = re.findall(quote_pattern, query)
        if quoted_matches:
            chars.has_quotes = True
            chars.exact_phrases = quoted_matches
            chars.query_type = "exact"
        
        # Check for dates (various formats)
        date_patterns = [
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',  # YYYY-MM-DD
            r'\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b',  # MM-DD-YYYY
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
            r'\b\d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',
            r'\b(today|yesterday|tomorrow|last week|this week|next week)\b'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                chars.has_dates = True
                break
        
        # Check for IDs (UUIDs, alphanumeric IDs)
        id_patterns = [
            r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b',  # UUID
            r'\b[A-Z0-9]{6,}\b',  # Uppercase alphanumeric ID
            r'\bID[-:\s]?\w+\b',  # ID followed by identifier
            r'#\w+',  # Hash-prefixed ID
        ]
        
        for pattern in id_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                chars.has_ids = True
                break
        
        # Check for numbers (prices, quantities, etc.)
        number_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',  # Dollar amounts
            r'\b\d+%',  # Percentages
            r'\b\d+(?:\.\d+)?\s*(gb|mb|kb|tb)\b',  # Data sizes
            r'\b\d{3,}\b',  # Large numbers
        ]
        
        for pattern in number_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                chars.has_numbers = True
                break
        
        # Determine query type
        if chars.has_quotes or chars.has_ids:
            chars.query_type = "exact"
        elif chars.has_dates or chars.has_numbers:
            chars.query_type = "hybrid"
        else:
            chars.query_type = "semantic"
        
        return chars
    
    def calculate_dynamic_weights(self, characteristics: QueryCharacteristics) -> Tuple[float, float]:
        """
        Calculate dynamic weights for vector vs keyword search.
        Carmelo's suggestion: adjust weights based on query characteristics.
        
        Returns:
            (vector_weight, keyword_weight) where both sum to 1.0
        """
        if characteristics.query_type == "exact":
            # Heavily favor keyword search for exact matches
            return 0.2, 0.8
        elif characteristics.query_type == "hybrid":
            # Balanced approach for mixed queries
            return 0.5, 0.5
        else:  # semantic
            # Favor vector search for conceptual queries
            return 0.8, 0.2
    
    def reciprocal_rank_fusion(
        self, 
        result_lists: List[List[Tuple]], 
        k: int = 60,
        normalize: bool = True
    ) -> Dict[str, float]:
        """
        Enhanced RRF with score normalization as suggested by Carmelo.
        
        Args:
            result_lists: List of result lists from different search methods
            k: RRF constant (typically 60)
            normalize: Whether to normalize final scores to [0, 1]
        
        Returns:
            Dictionary of document IDs to RRF scores
        """
        rrf_scores = defaultdict(float)
        
        for results in result_lists:
            for rank, result in enumerate(results, 1):
                # Extract document ID based on result format
                if isinstance(result, tuple) and len(result) >= 1:
                    doc_id = result[0]
                else:
                    continue
                
                # RRF formula: 1 / (k + rank)
                rrf_scores[doc_id] += 1 / (k + rank)
        
        if normalize and rrf_scores:
            # Normalize scores to [0, 1] range
            max_score = max(rrf_scores.values())
            min_score = min(rrf_scores.values())
            
            if max_score > min_score:
                for doc_id in rrf_scores:
                    rrf_scores[doc_id] = (rrf_scores[doc_id] - min_score) / (max_score - min_score)
            else:
                # All scores are the same
                for doc_id in rrf_scores:
                    rrf_scores[doc_id] = 0.5
        
        return dict(rrf_scores)
    
    def rerank_with_cross_encoder(
        self, 
        query: str, 
        documents: List[Tuple[str, str, Dict]], 
        top_k: int = 5
    ) -> List[Tuple[str, str, Dict, float]]:
        """
        Use cross-encoder to restore semantic order as Carmelo suggested.
        This fixes BM25's exact-token clutter issue.
        """
        if not self.cross_encoder or not documents:
            # No cross-encoder available, return as-is with dummy scores
            return [(d[0], d[1], d[2], 1.0) for d in documents[:top_k]]
        
        # Prepare pairs for cross-encoder
        pairs = [(query, doc[1]) for doc in documents]
        
        try:
            # Get semantic similarity scores
            scores = self.cross_encoder.predict(pairs)
            
            # Combine with documents and sort by score
            scored_docs = [
                (doc[0], doc[1], doc[2], float(score))
                for doc, score in zip(documents, scores)
            ]
            
            # Sort by cross-encoder score (descending)
            scored_docs.sort(key=lambda x: x[3], reverse=True)
            
            return scored_docs[:top_k]
        except Exception as e:
            print(f"Cross-encoder reranking failed: {e}")
            return [(d[0], d[1], d[2], 1.0) for d in documents[:top_k]]
    
    def search(
        self, 
        query: str, 
        k: int = 5,
        use_cross_encoder: bool = True,
        debug: bool = False
    ) -> List[Tuple[str, str, Dict[str, Any], float]]:
        """
        Enhanced hybrid search with all of Carmelo's suggestions.
        
        Args:
            query: Search query
            k: Number of results to return
            use_cross_encoder: Whether to use cross-encoder for reranking
            debug: Print debug information
        
        Returns:
            List of (doc_id, text, metadata, score) tuples
        """
        # Step 1: Analyze query characteristics
        characteristics = self.analyze_query(query)
        
        if debug:
            print(f"Query type: {characteristics.query_type}")
            if characteristics.exact_phrases:
                print(f"Exact phrases: {characteristics.exact_phrases}")
        
        # Step 2: Get dynamic weights
        vector_weight, keyword_weight = self.calculate_dynamic_weights(characteristics)
        
        if debug:
            print(f"Weights - Vector: {vector_weight:.2f}, Keyword: {keyword_weight:.2f}")
        
        # Step 3: Perform searches
        result_lists = []
        doc_content = {}  # Store document content for later use
        
        # Vector search (if weight > 0)
        if vector_weight > 0:
            vector_results = basic_search(query, k=k*3)  # Get more for fusion
            result_lists.append(vector_results)
            
            for doc_id, text, metadata in vector_results:
                doc_content[doc_id] = (text, metadata)
        
        # Keyword search (if weight > 0)
        if keyword_weight > 0 and self.keyword_index.enabled:
            # For exact phrases, search for them specifically
            if characteristics.exact_phrases:
                for phrase in characteristics.exact_phrases:
                    keyword_results = self.keyword_index.search(phrase, k=k*2)
                    formatted = [(doc_id, content, {}) for doc_id, _, content in keyword_results]
                    result_lists.append(formatted)
                    
                    for doc_id, _, content in keyword_results:
                        if doc_id not in doc_content:
                            doc_content[doc_id] = (content, {})
            else:
                keyword_results = self.keyword_index.search(query, k=k*3)
                formatted = [(doc_id, content, {}) for doc_id, _, content in keyword_results]
                result_lists.append(formatted)
                
                for doc_id, _, content in keyword_results:
                    if doc_id not in doc_content:
                        doc_content[doc_id] = (content, {})
        
        # Step 4: Apply RRF with normalization
        rrf_scores = self.reciprocal_rank_fusion(result_lists, normalize=True)
        
        if debug:
            print(f"RRF produced {len(rrf_scores)} unique documents")
        
        # Step 5: Weight the RRF scores based on search method preference
        weighted_scores = {}
        for doc_id, rrf_score in rrf_scores.items():
            # Adjust score based on which search method found it
            found_in_vector = any(doc_id == r[0] for r in result_lists[0]) if len(result_lists) > 0 else False
            found_in_keyword = any(
                doc_id == r[0] 
                for results in result_lists[1:] 
                for r in results
            ) if len(result_lists) > 1 else False
            
            if found_in_vector and found_in_keyword:
                # Found in both - use weighted average
                weighted_scores[doc_id] = rrf_score
            elif found_in_vector:
                # Only in vector - adjust by vector weight
                weighted_scores[doc_id] = rrf_score * vector_weight
            else:
                # Only in keyword - adjust by keyword weight
                weighted_scores[doc_id] = rrf_score * keyword_weight
        
        # Step 6: Create initial ranking
        candidates = []
        for doc_id, score in weighted_scores.items():
            if doc_id in doc_content:
                text, metadata = doc_content[doc_id]
                candidates.append((doc_id, text, metadata, score))
        
        # Sort by weighted RRF score
        candidates.sort(key=lambda x: x[3], reverse=True)
        
        # Step 7: Apply cross-encoder reranking (Carmelo's suggestion to fix BM25 clutter)
        if use_cross_encoder and self.cross_encoder:
            # Take top candidates for reranking (to limit computation)
            rerank_candidates = [(c[0], c[1], c[2]) for c in candidates[:k*2]]
            
            if debug:
                print(f"Reranking top {len(rerank_candidates)} with cross-encoder")
            
            final_results = self.rerank_with_cross_encoder(query, rerank_candidates, top_k=k)
        else:
            final_results = candidates[:k]
        
        if debug:
            print(f"Returning {len(final_results)} results")
            for i, (doc_id, _, _, score) in enumerate(final_results[:3], 1):
                print(f"  {i}. {doc_id[:20]}... (score: {score:.3f})")
        
        return final_results
    
    def batch_search(
        self, 
        queries: List[str], 
        k: int = 5
    ) -> Dict[str, List[Tuple]]:
        """Batch search multiple queries efficiently."""
        results = {}
        
        for query in queries:
            results[query] = self.search(query, k=k, debug=False)
        
        return results


def benchmark_enhanced_search():
    """Benchmark the enhanced hybrid search."""
    import time
    import statistics
    
    print("=" * 60)
    print("BENCHMARKING ENHANCED HYBRID SEARCH (Carmelo's Suggestions)")
    print("=" * 60)
    
    searcher = DynamicHybridSearch()
    
    # Test queries with different characteristics
    test_queries = [
        # Exact match queries (should favor keyword)
        '"cognitive AI"',
        'ID-12345',
        '"vector databases" Pinecone',
        
        # Date/number queries (should use hybrid)
        'revenue $2.1 million 2024',
        'meeting January 15 2024',
        '85% recall rate',
        
        # Semantic queries (should favor vector)
        'How does memory work in AI systems?',
        'Benefits of cognitive computing',
        'Transform education with technology',
        
        # Mixed queries
        'Josh monthly payment $2,100',
        '"18-24 month" objective equity',
    ]
    
    results_summary = []
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        # Analyze characteristics
        chars = searcher.analyze_query(query)
        print(f"Type: {chars.query_type}")
        
        # Time the search
        t0 = time.time()
        results = searcher.search(query, k=5, debug=True)
        dt = (time.time() - t0) * 1000
        
        print(f"Latency: {dt:.1f}ms")
        print(f"Results: {len(results)}")
        
        results_summary.append({
            'query': query,
            'type': chars.query_type,
            'latency_ms': dt,
            'results': len(results)
        })
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    
    latencies = [r['latency_ms'] for r in results_summary]
    
    print(f"Average latency: {statistics.mean(latencies):.1f}ms")
    print(f"Median latency: {statistics.median(latencies):.1f}ms")
    print(f"Min latency: {min(latencies):.1f}ms")
    print(f"Max latency: {max(latencies):.1f}ms")
    
    # Group by query type
    by_type = defaultdict(list)
    for r in results_summary:
        by_type[r['type']].append(r['latency_ms'])
    
    print("\nLatency by query type:")
    for qtype, lats in by_type.items():
        print(f"  {qtype}: {statistics.mean(lats):.1f}ms avg")
    
    print("\n✅ Enhanced hybrid search with Carmelo's suggestions is ready!")
    print("Features implemented:")
    print("  • Dynamic weighting based on query characteristics")
    print("  • Enhanced RRF with score normalization")
    print("  • Cross-encoder reranking to fix BM25 clutter")
    print("  • Special handling for IDs, dates, and quoted phrases")


if __name__ == "__main__":
    benchmark_enhanced_search()
