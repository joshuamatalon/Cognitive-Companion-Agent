"""
Dynamic query weighting based on query characteristics.
Implements Carmelo's suggestion for handling IDs, dates, and quoted phrases.
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib

@dataclass
class QueryCharacteristics:
    """Characteristics of a search query for dynamic weighting."""
    has_quotes: bool = False
    has_ids: bool = False
    has_dates: bool = False
    has_numbers: bool = False
    has_special_terms: bool = False
    quoted_phrases: List[str] = None
    detected_ids: List[str] = None
    detected_dates: List[str] = None
    query_type: str = "general"  # general, exact, navigational, temporal

class DynamicWeightCalculator:
    """
    Calculate dynamic weights for hybrid search based on query characteristics.
    Implements smart detection of IDs, dates, and quoted phrases.
    """
    
    # Patterns for detection
    UUID_PATTERN = re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I)
    ID_PATTERNS = [
        re.compile(r'\b[A-Z]{2,}-\d+\b'),  # JIRA-style: ABC-123
        re.compile(r'\b\d{6,}\b'),  # Long numbers (likely IDs)
        re.compile(r'\b[A-Z0-9]{8,}\b'),  # Alphanumeric IDs
        re.compile(r'#\d+'),  # Hash IDs: #12345
    ]
    
    DATE_PATTERNS = [
        re.compile(r'\b\d{4}-\d{1,2}-\d{1,2}\b'),  # 2024-01-15
        re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'),  # 01/15/2024
        re.compile(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2},? \d{4}\b', re.I),
        re.compile(r'\b(january|february|march|april|may|june|july|august|september|october|november|december) \d{1,2},? \d{4}\b', re.I),
        re.compile(r'\b(today|yesterday|tomorrow|last week|this week|next week|last month|this month)\b', re.I),
    ]
    
    QUOTED_PHRASE_PATTERN = re.compile(r'"([^"]+)"')
    
    def __init__(self):
        self.default_weights = {
            "general": {"vector": 0.7, "keyword": 0.3},
            "exact": {"vector": 0.3, "keyword": 0.7},
            "navigational": {"vector": 0.2, "keyword": 0.8},
            "temporal": {"vector": 0.5, "keyword": 0.5}
        }
    
    def analyze_query(self, query: str) -> QueryCharacteristics:
        """Analyze query to detect special characteristics."""
        chars = QueryCharacteristics()
        
        # Check for quoted phrases
        quoted_matches = self.QUOTED_PHRASE_PATTERN.findall(query)
        if quoted_matches:
            chars.has_quotes = True
            chars.quoted_phrases = quoted_matches
        
        # Check for UUIDs
        if self.UUID_PATTERN.search(query):
            chars.has_ids = True
            chars.detected_ids = self.UUID_PATTERN.findall(query)
        
        # Check for other ID patterns
        for pattern in self.ID_PATTERNS:
            matches = pattern.findall(query)
            if matches:
                chars.has_ids = True
                if chars.detected_ids is None:
                    chars.detected_ids = []
                chars.detected_ids.extend(matches)
        
        # Check for dates
        for pattern in self.DATE_PATTERNS:
            matches = pattern.findall(query)
            if matches:
                chars.has_dates = True
                if chars.detected_dates is None:
                    chars.detected_dates = []
                chars.detected_dates.extend(matches if isinstance(matches[0], str) else [m[0] if isinstance(m, tuple) else m for m in matches])
        
        # Check for numbers
        if re.search(r'\b\d+\b', query):
            chars.has_numbers = True
        
        # Determine query type
        if chars.has_quotes or chars.has_ids:
            chars.query_type = "exact"
        elif chars.has_ids and not chars.has_quotes:
            chars.query_type = "navigational"
        elif chars.has_dates:
            chars.query_type = "temporal"
        else:
            chars.query_type = "general"
        
        return chars
    
    def calculate_weights(
        self, 
        query: str,
        force_exact: bool = False
    ) -> Tuple[float, float]:
        """
        Calculate dynamic weights for vector and keyword search.
        
        Returns:
            Tuple of (vector_weight, keyword_weight) that sum to 1.0
        """
        # Analyze query characteristics
        chars = self.analyze_query(query)
        
        # Force exact matching if requested
        if force_exact:
            return 0.1, 0.9
        
        # Get base weights for query type
        weights = self.default_weights[chars.query_type].copy()
        
        # Adjust weights based on specific characteristics
        adjustments = self._calculate_adjustments(chars)
        
        # Apply adjustments
        vector_weight = weights["vector"] * adjustments["vector_mult"]
        keyword_weight = weights["keyword"] * adjustments["keyword_mult"]
        
        # Normalize to sum to 1.0
        total = vector_weight + keyword_weight
        if total > 0:
            vector_weight /= total
            keyword_weight /= total
        else:
            vector_weight, keyword_weight = 0.5, 0.5
        
        return vector_weight, keyword_weight
    
    def _calculate_adjustments(self, chars: QueryCharacteristics) -> Dict[str, float]:
        """Calculate weight adjustments based on characteristics."""
        adjustments = {
            "vector_mult": 1.0,
            "keyword_mult": 1.0
        }
        
        # Strong keyword boost for quoted phrases
        if chars.has_quotes:
            adjustments["keyword_mult"] *= 2.0
            adjustments["vector_mult"] *= 0.5
        
        # Moderate keyword boost for IDs
        if chars.has_ids:
            adjustments["keyword_mult"] *= 1.5
            adjustments["vector_mult"] *= 0.7
        
        # Balanced boost for dates (both methods can be useful)
        if chars.has_dates:
            adjustments["keyword_mult"] *= 1.2
            adjustments["vector_mult"] *= 1.1
        
        return adjustments
    
    def get_query_strategy(self, query: str) -> Dict[str, any]:
        """
        Get complete search strategy for a query.
        
        Returns:
            Dictionary with weights and search recommendations
        """
        chars = self.analyze_query(query)
        vector_weight, keyword_weight = self.calculate_weights(query)
        
        strategy = {
            "query": query,
            "characteristics": chars,
            "weights": {
                "vector": vector_weight,
                "keyword": keyword_weight
            },
            "recommendations": []
        }
        
        # Add specific recommendations
        if chars.has_quotes:
            strategy["recommendations"].append("Use exact phrase matching for quoted terms")
            strategy["exact_phrases"] = chars.quoted_phrases
        
        if chars.has_ids:
            strategy["recommendations"].append("Prioritize exact ID matching")
            strategy["ids_to_match"] = chars.detected_ids
        
        if chars.has_dates:
            strategy["recommendations"].append("Include temporal filtering")
            strategy["temporal_context"] = chars.detected_dates
        
        # Suggest using cross-encoder for reranking if mixed signals
        if chars.query_type == "general" and (chars.has_numbers or len(query.split()) > 5):
            strategy["recommendations"].append("Use cross-encoder reranking")
            strategy["use_reranking"] = True
        else:
            strategy["use_reranking"] = False
        
        return strategy

class EnhancedHybridSearch:
    """
    Enhanced hybrid search with dynamic weighting.
    Implements Carmelo's suggestions for better search quality.
    """
    
    def __init__(self):
        self.weight_calculator = DynamicWeightCalculator()
        self._cache = {}
    
    def search(
        self,
        query: str,
        k: int = 5,
        use_rrf: bool = True,
        override_weights: Optional[Tuple[float, float]] = None
    ) -> List[Tuple[str, str, Dict, float]]:
        """
        Perform enhanced hybrid search with dynamic weighting.
        
        Args:
            query: Search query
            k: Number of results
            use_rrf: Use Reciprocal Rank Fusion
            override_weights: Optional (vector_weight, keyword_weight) override
            
        Returns:
            List of (doc_id, text, metadata, score) tuples
        """
        # Check cache
        cache_key = hashlib.md5(f"{query}_{k}_{use_rrf}".encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get search strategy
        strategy = self.weight_calculator.get_query_strategy(query)
        
        # Use override weights if provided, otherwise use calculated
        if override_weights:
            vector_weight, keyword_weight = override_weights
        else:
            vector_weight = strategy["weights"]["vector"]
            keyword_weight = strategy["weights"]["keyword"]
        
        # Import search functions
        from search_enhancements import enhanced_search, hybrid_search
        from production_search import ProductionAdvancedSearch
        
        # Use production search for complex queries
        if strategy.get("use_reranking", False):
            searcher = ProductionAdvancedSearch()
            results = searcher.search(query, k=k, use_cross_encoder=True)
            # Convert to expected format
            results = [(r[0], r[1], r[2], 1.0) for r in results]
        else:
            # Use regular hybrid search with dynamic weights
            results = hybrid_search(
                query=query,
                k=k,
                alpha=vector_weight,  # Vector weight
                use_rrf=use_rrf
            )
        
        # Handle exact phrase matching if needed
        if strategy.get("exact_phrases"):
            results = self._boost_exact_matches(results, strategy["exact_phrases"])
        
        # Handle ID matching if needed
        if strategy.get("ids_to_match"):
            results = self._boost_id_matches(results, strategy["ids_to_match"])
        
        # Cache results
        self._cache[cache_key] = results
        
        # Limit cache size
        if len(self._cache) > 1000:
            # Remove oldest entries
            keys = list(self._cache.keys())
            for key in keys[:100]:
                del self._cache[key]
        
        return results
    
    def _boost_exact_matches(
        self,
        results: List[Tuple],
        exact_phrases: List[str]
    ) -> List[Tuple]:
        """Boost results containing exact phrases."""
        boosted = []
        
        for doc_id, text, metadata, score in results:
            boost = 1.0
            text_lower = text.lower()
            
            for phrase in exact_phrases:
                if phrase.lower() in text_lower:
                    boost *= 1.5  # 50% boost for each exact match
            
            boosted.append((doc_id, text, metadata, score * boost))
        
        # Re-sort by boosted scores
        boosted.sort(key=lambda x: x[3], reverse=True)
        return boosted
    
    def _boost_id_matches(
        self,
        results: List[Tuple],
        ids: List[str]
    ) -> List[Tuple]:
        """Boost results containing specific IDs."""
        boosted = []
        
        for doc_id, text, metadata, score in results:
            boost = 1.0
            
            # Check document ID
            for id_to_match in ids:
                if id_to_match in doc_id:
                    boost *= 2.0  # Strong boost for ID in document ID
                elif id_to_match in text:
                    boost *= 1.3  # Moderate boost for ID in text
            
            boosted.append((doc_id, text, metadata, score * boost))
        
        # Re-sort by boosted scores
        boosted.sort(key=lambda x: x[3], reverse=True)
        return boosted
    
    def explain_strategy(self, query: str) -> str:
        """
        Explain the search strategy for a query.
        Useful for debugging and understanding.
        """
        strategy = self.weight_calculator.get_query_strategy(query)
        
        explanation = []
        explanation.append(f"Query: '{query}'")
        explanation.append(f"Type: {strategy['characteristics'].query_type}")
        explanation.append(f"Weights: Vector={strategy['weights']['vector']:.2f}, Keyword={strategy['weights']['keyword']:.2f}")
        
        if strategy['characteristics'].has_quotes:
            explanation.append(f"Quoted phrases: {strategy['characteristics'].quoted_phrases}")
        
        if strategy['characteristics'].has_ids:
            explanation.append(f"IDs detected: {strategy['characteristics'].detected_ids}")
        
        if strategy['characteristics'].has_dates:
            explanation.append(f"Dates detected: {strategy['characteristics'].detected_dates}")
        
        if strategy['recommendations']:
            explanation.append("Recommendations:")
            for rec in strategy['recommendations']:
                explanation.append(f"  - {rec}")
        
        return "\n".join(explanation)

# Example usage and testing
def test_dynamic_weighting():
    """Test the dynamic weighting system."""
    calculator = DynamicWeightCalculator()
    enhanced = EnhancedHybridSearch()
    
    test_queries = [
        "What is cognitive AI?",  # General query
        '"exact phrase match"',  # Quoted phrase
        "Find document ABC-123",  # ID query
        "Results from January 2024",  # Temporal query
        "User #42351 payment history",  # Mixed: ID + domain
        '"vector databases" Pinecone',  # Mixed: quoted + term
        "8f3e2401-d0b8-4b3d-9c5e-6a2f1e3b4c5d",  # UUID
    ]
    
    print("=" * 60)
    print("DYNAMIC QUERY WEIGHTING TEST")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        # Analyze characteristics
        chars = calculator.analyze_query(query)
        vector_weight, keyword_weight = calculator.calculate_weights(query)
        
        print(f"Type: {chars.query_type}")
        print(f"Weights: Vector={vector_weight:.2f}, Keyword={keyword_weight:.2f}")
        
        if chars.has_quotes:
            print(f"Quoted: {chars.quoted_phrases}")
        if chars.has_ids:
            print(f"IDs: {chars.detected_ids}")
        if chars.has_dates:
            print(f"Dates: {chars.detected_dates}")
        
        # Show strategy
        print("\nStrategy explanation:")
        print(enhanced.explain_strategy(query))
    
    print("\n" + "=" * 60)
    print("Dynamic weighting system ready!")
    print("This addresses Carmelo's feedback about IDs/dates/quotes")
    print("=" * 60)

if __name__ == "__main__":
    test_dynamic_weighting()
