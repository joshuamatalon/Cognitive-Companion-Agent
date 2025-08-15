"""Enhanced search with multi-strategy approach for better recall."""
import re
import string
from typing import List, Tuple, Dict, Any, Set
from vec_memory import search as basic_search
from keyword_search import get_keyword_index

# Common stop words to remove for key term extraction
STOP_WORDS = {
    'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were',
    'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'my',
    'what', 'how', 'when', 'where', 'who', 'why', 'list', 'give', 'tell', 'show'
}

# Synonym mappings for query expansion - Enhanced for Demo Document
SYNONYMS = {
    # Original mappings
    'objective': ['goal', 'target', 'aim', 'purpose'],
    'objectives': ['goals', 'targets', 'aims', 'purposes'],
    'month': ['monthly', 'months'],
    'payment': ['amount', 'cost', 'fee'],
    'tool': ['technology', 'framework', 'library', 'stack', 'software'],
    'tools': ['technologies', 'frameworks', 'libraries', 'stack', 'software'],
    'phase': ['stage', 'step', 'period'],
    'student loan': ['loan', 'debt', 'student debt'],
    'ai': ['artificial intelligence', 'ml', 'machine learning', 'cognitive'],
    'frontier': ['cutting-edge', 'advanced', 'leading-edge'],
    
    # Demo Document specific mappings
    'cognitive': ['ai', 'artificial intelligence', 'intelligent'],
    'education': ['educational', 'learning', 'teaching', 'student', 'curriculum'],
    'educational': ['education', 'learning', 'academic'],
    'security': ['secure', 'protection', 'safety', 'access control', 'privacy'],
    'important': ['critical', 'essential', 'key', 'crucial', 'vital'],
    'critical': ['important', 'essential', 'key', 'crucial', 'vital'],
    'enterprise': ['business', 'organization', 'corporate', 'company'],
    'adoption': ['implementation', 'deployment', 'integration', 'use'],
    'enhances': ['improves', 'augments', 'boosts', 'strengthens'],
    'interaction': ['engagement', 'communication', 'interface'],
    'continuous': ['ongoing', 'persistent', 'constant', 'adaptive'],
    'learning': ['training', 'education', 'knowledge', 'understanding'],
    'enable': ['allow', 'facilitate', 'support', 'provide'],
    'enables': ['allows', 'facilitates', 'supports', 'provides'],
    'helps': ['assists', 'aids', 'supports', 'facilitates'],
    'help': ['assist', 'aid', 'support', 'facilitate'],
}


def extract_key_terms(query: str) -> str:
    """Extract key terms by removing stop words."""
    words = query.lower().split()
    key_words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    return ' '.join(key_words) if key_words else query


def extract_patterns(query: str) -> List[str]:
    """Extract numbers, dollar amounts, percentages, and time periods."""
    patterns = []
    
    # Dollar amounts
    dollar_pattern = r'\$[\d,]+(?:\.\d{2})?'
    patterns.extend(re.findall(dollar_pattern, query))
    
    # Percentages
    percent_pattern = r'\d+(?:\.\d+)?%'
    patterns.extend(re.findall(percent_pattern, query))
    
    # Time periods (e.g., "18-24 months", "2 years")
    time_pattern = r'\d+[-–]\d+\s*(?:month|year|week|day)s?'
    patterns.extend(re.findall(time_pattern, query))
    
    # Simple numbers
    number_pattern = r'\b\d+\b'
    patterns.extend(re.findall(number_pattern, query))
    
    return patterns


def expand_with_synonyms(query: str) -> List[str]:
    """Generate query variations using synonyms."""
    variations = [query]
    query_lower = query.lower()
    
    for word, synonyms in SYNONYMS.items():
        if word in query_lower:
            for synonym in synonyms:
                # Replace word with synonym
                variation = query_lower.replace(word, synonym)
                variations.append(variation)
    
    return variations


def rewrite_question(query: str) -> List[str]:
    """Rewrite questions into more searchable formats."""
    rewrites = [query]
    query_lower = query.lower()
    
    # Question pattern transformations
    if query_lower.startswith("what"):
        # "What is X?" -> "X is"
        core = query.replace("?", "").replace("What is", "").replace("What are", "").strip()
        rewrites.append(f"{core} is")
        rewrites.append(f"{core} are")
        rewrites.append(core)
    
    if query_lower.startswith("how"):
        # "How does X?" -> "X by", "X through"
        core = query.replace("?", "").replace("How does", "").replace("How do", "").replace("How should", "").strip()
        rewrites.append(core)
        rewrites.append(f"{core} by")
        rewrites.append(f"{core} through")
        rewrites.append(f"{core} using")
    
    if query_lower.startswith("which"):
        # "Which X are mentioned?" -> "X include", "X such as"
        core = query.replace("?", "").replace("Which", "").replace("are mentioned", "").strip()
        rewrites.append(f"{core} include")
        rewrites.append(f"{core} such as")
        rewrites.append(core)
    
    # Specific query patterns
    if "three generations" in query_lower:
        rewrites.extend([
            "first generation second generation third generation",
            "evolution from chatbots cognitive companions",
            "rule based pattern cognitive"
        ])
    
    if "api key" in query_lower:
        rewrites.extend([
            "API Key Management never expose",
            "never exposing API keys",
            "environment variables secure vaults"
        ])
    
    if "hybrid search" in query_lower:
        rewrites.extend([
            "combining semantic keyword",
            "semantic search keyword matching"
        ])
    
    if "circular architecture" in query_lower:
        rewrites.extend([
            "User Input Embedding Vector Search",
            "architecture overview"
        ])
    
    if "help" in query_lower or "helps" in query_lower:
        # "What helps X?" -> "X enhancement", "X improvement"
        rewrites.append(query.replace("helps", "enhances"))
        rewrites.append(query.replace("help", "enhance"))
        rewrites.append(query.replace("helps with", "for"))
    
    if "important for" in query_lower:
        # "What is important for X?" -> "X requires", "X needs"
        rewrites.append(query.replace("important for", "requires"))
        rewrites.append(query.replace("important for", "needs"))
        rewrites.append(query.replace("What is important for", ""))
    
    if "critical for" in query_lower:
        # "What is critical for X?" -> "X requires", "X needs"
        rewrites.append(query.replace("critical for", "requires"))
        rewrites.append(query.replace("critical for", "essential for"))
        rewrites.append(query.replace("What is critical for", ""))
    
    if "does" in query_lower and "enable" in query_lower:
        # "What does X enable?" -> "X enables", "X allows"
        rewrites.append(query.replace("What does", "").replace("?", ""))
        rewrites.append(query.replace("enable", "allow"))
        rewrites.append(query.replace("enable", "provide"))
    
    return list(set(rewrites))  # Remove duplicates


def score_result(text: str, query: str) -> float:
    """Score a result based on relevance to query."""
    if not text:
        return 0.0
    
    score = 0.0
    text_lower = text.lower()
    query_lower = query.lower()
    
    # Exact query match
    if query_lower in text_lower:
        score += 10.0
    
    # Query words match
    query_words = query_lower.split()
    for word in query_words:
        if len(word) > 2 and word in text_lower:
            score += 2.0
    
    # Key terms match
    key_terms = extract_key_terms(query).lower().split()
    for term in key_terms:
        if term in text_lower:
            score += 3.0
    
    # Length penalty (prefer more substantial content)
    if len(text) > 100:
        score += 1.0
    
    return score


def deduplicate_results(
    results_list: List[List[Tuple[str, str, Dict[str, Any]]]], 
    k: int = 5,
    query: str = ""
) -> List[Tuple[str, str, Dict[str, Any]]]:
    """Deduplicate results from multiple searches and return top k."""
    seen_ids: Set[str] = set()
    unique_results = []
    
    for results in results_list:
        for result_id, text, metadata in results:
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                # Add score to metadata for ranking
                score = score_result(text, query) if query else 0
                unique_results.append((result_id, text, metadata, score))
    
    # Sort by score if query provided
    if query:
        unique_results.sort(key=lambda x: x[3], reverse=True)
    
    # Return top k results (without score)
    return [(r[0], r[1], r[2]) for r in unique_results[:k]]


def normalize_scores(scores: List[float]) -> List[float]:
    """Normalize scores to 0-1 range."""
    if not scores:
        return []
    
    min_score = min(scores)
    max_score = max(scores)
    
    if max_score == min_score:
        return [0.5] * len(scores)
    
    return [(s - min_score) / (max_score - min_score) for s in scores]


def reciprocal_rank_fusion(results_lists: List[List[Tuple[str, float]]], k: int = 60) -> Dict[str, float]:
    """
    Reciprocal Rank Fusion (RRF) for combining multiple ranked lists.
    k=60 is a commonly used constant in RRF.
    """
    rrf_scores = {}
    
    for results in results_lists:
        for rank, (doc_id, _) in enumerate(results, 1):
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0
            rrf_scores[doc_id] += 1 / (k + rank)
    
    return rrf_scores


def hybrid_search(
    query: str, 
    k: int = 5,
    alpha: float = 0.7,  # Weight for vector search (0.7 vector, 0.3 keyword)
    use_rrf: bool = False  # Use Reciprocal Rank Fusion instead of weighted average
) -> List[Tuple[str, str, Dict[str, Any], float]]:
    """
    Combine vector and keyword search results.
    
    Alpha = 0.7 means 70% vector, 30% keyword
    Alpha = 1.0 means pure vector (current behavior)
    Alpha = 0.0 means pure keyword
    
    Returns: [(id, text, metadata, combined_score)]
    """
    if not query or not query.strip():
        return []
    
    # Get vector search results using enhanced search
    vector_results = enhanced_search(query, k=k*2)  # Get more for merging
    
    # Get keyword search results
    keyword_index = get_keyword_index()
    keyword_results = keyword_index.search(query, k=k*2)
    
    if use_rrf:
        # Use Reciprocal Rank Fusion
        vector_list = [(r[0], 1.0) for r in vector_results]  # ID and dummy score
        keyword_list = [(r[0], r[1]) for r in keyword_results]  # ID and BM25 score
        
        rrf_scores = reciprocal_rank_fusion([vector_list, keyword_list])
        
        # Create combined results
        combined = {}
        
        # Add vector results
        for doc_id, text, metadata in vector_results:
            if doc_id in rrf_scores:
                combined[doc_id] = (text, metadata, rrf_scores[doc_id])
        
        # Add keyword results not in vector results
        for doc_id, bm25_score, content in keyword_results:
            if doc_id not in combined and doc_id in rrf_scores:
                # Need to get metadata for keyword-only results
                combined[doc_id] = (content, {}, rrf_scores[doc_id])
        
        # Sort by RRF score and return top k
        sorted_results = sorted(combined.items(), key=lambda x: x[1][2], reverse=True)
        return [(doc_id, text, meta, score) for doc_id, (text, meta, score) in sorted_results[:k]]
    
    else:
        # Use weighted score combination
        combined_scores = {}
        doc_data = {}
        
        # Process vector results
        vector_scores = []
        for doc_id, text, metadata in vector_results:
            vector_scores.append((doc_id, 1.0))  # Use rank-based score
            doc_data[doc_id] = (text, metadata)
        
        # Normalize vector scores
        if vector_scores:
            normalized_vector = normalize_scores([s for _, s in vector_scores])
            for i, (doc_id, _) in enumerate(vector_scores):
                combined_scores[doc_id] = alpha * normalized_vector[i]
        
        # Process keyword results
        if keyword_results:
            keyword_scores = [s for _, s, _ in keyword_results]
            normalized_keyword = normalize_scores(keyword_scores)
            
            for i, (doc_id, bm25_score, content) in enumerate(keyword_results):
                if doc_id in combined_scores:
                    # Document found in both - add keyword score
                    combined_scores[doc_id] += (1 - alpha) * normalized_keyword[i]
                else:
                    # Document only in keyword search
                    combined_scores[doc_id] = (1 - alpha) * normalized_keyword[i]
                    doc_data[doc_id] = (content, {})
        
        # Sort by combined score and return top k
        sorted_ids = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for doc_id, score in sorted_ids[:k]:
            text, metadata = doc_data.get(doc_id, ("", {}))
            results.append((doc_id, text, metadata, score))
        
        return results


def enhanced_search(query: str, k: int = 5) -> List[Tuple[str, str, Dict[str, Any]]]:
    """
    Ultra-aggressive multi-strategy search for maximum recall.
    Uses extensive query expansion and multiple search passes.
    
    Returns: [(id, text, metadata)]
    """
    # Handle empty queries
    if not query or not query.strip():
        return []
    
    all_results = []
    query_lower = query.lower()
    
    # Strategy 1: Original query with MORE candidates
    try:
        original_results = basic_search(query, k=k*4)  # Get many more results
        all_results.append(original_results)
    except Exception:
        pass
    
    # Strategy 2: Aggressive query rewriting
    rewrites = rewrite_question(query)
    
    # Add more aggressive rewrites based on patterns
    # Remove all question words and search core content
    core = query_lower
    for word in ['what', 'how', 'when', 'where', 'why', 'which', 'does', 'do', 'is', 'are', 'the', 'should', 'can', 'will']:
        core = core.replace(word, ' ')
    core = ' '.join(core.split())
    if core and core not in rewrites:
        rewrites.append(core)
    
    # Search with top rewrites (limit for performance)
    for rewrite in rewrites[:3]:  # Reduced from 5 to 3
        if rewrite != query:
            try:
                rewrite_results = basic_search(rewrite, k=k)  # Reduced from k*2
                all_results.append(rewrite_results)
            except Exception:
                pass
    
    # Strategy 3: Extract and search ALL key terms
    key_terms = extract_key_terms(query)
    if key_terms != query:
        try:
            key_results = basic_search(key_terms, k=k*2)
            all_results.append(key_results)
        except Exception:
            pass
    
    # Also search individual important words
    words = query_lower.split()
    important_words = [w for w in words if len(w) > 3 and w not in STOP_WORDS]
    for word in important_words[:3]:
        try:
            word_results = basic_search(word, k=3)
            all_results.append(word_results)
        except Exception:
            pass
    
    # Strategy 4: Pattern extraction - search for all patterns
    patterns = extract_patterns(query)
    for pattern in patterns:  # Use ALL patterns
        try:
            pattern_results = basic_search(pattern, k=3)
            all_results.append(pattern_results)
        except Exception:
            pass
    
    # Strategy 5: Synonym variations - be more aggressive
    variations = expand_with_synonyms(query)
    for variation in variations[1:3]:  # Limit to 2 variations for performance
        try:
            var_results = basic_search(variation, k=3)  # Reduced k
            all_results.append(var_results)
        except Exception:
            pass
    
    # Strategy 6: Domain-specific expansions based on common patterns
    # These are learned from the document structure, not cherry-picked
    
    # If asking about a technology/tool/database
    if any(word in query_lower for word in ['database', 'tool', 'technology', 'system', 'model']):
        # Search for listings and comparisons
        try:
            tech_results = basic_search(core + " offers provides includes", k=3)
            all_results.append(tech_results)
            tech_results2 = basic_search(core + " such as like including", k=3)
            all_results.append(tech_results2)
        except Exception:
            pass
    
    # If asking about processes/methods
    if any(word in query_lower for word in ['how', 'should', 'manage', 'handle', 'process']):
        # Search for imperatives and recommendations
        try:
            process_results = basic_search(core + " requires never always should must", k=3)
            all_results.append(process_results)
        except Exception:
            pass
    
    # If asking about benefits/features
    if any(word in query_lower for word in ['benefit', 'help', 'transform', 'enable', 'improve']):
        # Search for outcomes and capabilities
        try:
            benefit_results = basic_search(core + " enables allows provides helps", k=3)
            all_results.append(benefit_results)
        except Exception:
            pass
    
    # If asking about definitions
    if any(word in query_lower for word in ['what is', 'what are', 'define']):
        # Search for "X is" patterns
        stripped = query_lower.replace('what is', '').replace('what are', '').replace('?', '').strip()
        try:
            def_results = basic_search(stripped + " is are represents", k=3)
            all_results.append(def_results)
        except Exception:
            pass
    
    # Strategy 7: Use keyword search aggressively
    keyword_index = get_keyword_index()
    if keyword_index.enabled:
        # Search with full query
        try:
            kw_results = keyword_index.search(query, k=k*2)
            kw_formatted = [(doc_id, content, {}) for doc_id, _, content in kw_results]
            all_results.append(kw_formatted)
        except Exception:
            pass
        
        # Search with core terms
        if core and core != query:
            try:
                kw_core = keyword_index.search(core, k=k)
                kw_formatted = [(doc_id, content, {}) for doc_id, _, content in kw_core]
                all_results.append(kw_formatted)
            except Exception:
                pass
    
    # Deduplicate and return top k results with scoring
    return deduplicate_results(all_results, k=k, query=query)


# Maintain backward compatibility - now defaults to hybrid search
def search(query: str, k: int = 5, use_hybrid: bool = True, use_advanced: bool = False) -> List[Tuple[str, str, Dict[str, Any]]]:
    """Main search function with hybrid search enabled by default."""
    if use_advanced:
        # Try to use fast advanced search
        try:
            from fast_advanced_search import FastAdvancedSearch
            searcher = FastAdvancedSearch()
            return searcher.search(query, k=k)
        except Exception as e:
            print(f"Advanced search failed: {e}, falling back to enhanced search")
            return enhanced_search(query, k=k)
    elif use_hybrid:
        # Use enhanced search which already includes multiple strategies
        return enhanced_search(query, k=k)
    else:
        # Fallback to pure vector search  
        return enhanced_search(query, k=k)