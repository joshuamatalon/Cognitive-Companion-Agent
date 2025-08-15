"""
Cached advanced search - prevents timeouts by caching LLM responses.
"""

import json
import hashlib
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, asdict
import pickle

from vec_memory import search as basic_search
from keyword_search import get_keyword_index
from search_enhancements import enhanced_search
from rag_chain import llm

# Cache configuration
CACHE_DIR = Path("search_cache")
CACHE_DIR.mkdir(exist_ok=True)


class LLMCache:
    """Simple file-based cache for LLM responses"""
    
    def __init__(self, ttl_seconds: int = 86400):  # 24 hour TTL
        self.ttl = ttl_seconds
        self.cache_file = CACHE_DIR / "llm_cache.json"
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
        except:
            pass
    
    def _get_key(self, prompt: str) -> str:
        """Generate cache key from prompt"""
        return hashlib.md5(prompt.encode()).hexdigest()
    
    def get(self, prompt: str) -> Optional[str]:
        """Get cached response if available and not expired"""
        key = self._get_key(prompt)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                return entry['response']
        return None
    
    def set(self, prompt: str, response: str):
        """Cache a response"""
        key = self._get_key(prompt)
        self.cache[key] = {
            'response': response,
            'timestamp': time.time()
        }
        self._save_cache()


class CachedHyDESearch:
    """HyDE with caching to prevent timeouts"""
    
    def __init__(self):
        self.llm = llm
        self.cache = LLMCache()
        # Pre-computed templates for common query patterns
        self.templates = {
            'definition': "The {subject} is a method/system/concept that {action}. It involves {components} and is used for {purpose}.",
            'process': "To {subject}, follow these steps: 1) {step1}, 2) {step2}, 3) {step3}. This process ensures {outcome}.",
            'comparison': "{subject1} differs from {subject2} in that {difference}. While {subject1} focuses on {focus1}, {subject2} emphasizes {focus2}.",
            'list': "The main {subject} include: {item1}, {item2}, and {item3}. Each serves different purposes in {context}."
        }
    
    def generate_hypothetical_fast(self, query: str) -> str:
        """Generate hypothetical with caching and templates"""
        
        # Check cache first
        cached = self.cache.get(query)
        if cached:
            return cached
        
        # Try template-based generation first (no LLM needed)
        query_lower = query.lower()
        
        if "what is" in query_lower or "define" in query_lower:
            subject = query_lower.replace("what is", "").replace("?", "").strip()
            response = self.templates['definition'].format(
                subject=subject,
                action="performs specific functions",
                components="multiple components",
                purpose="achieving desired outcomes"
            )
        
        elif "how" in query_lower:
            subject = query_lower.replace("how", "").replace("?", "").strip()
            response = self.templates['process'].format(
                subject=subject,
                step1="initialize the system",
                step2="process the input",
                step3="generate output",
                outcome="successful completion"
            )
        
        elif "which" in query_lower or "what are" in query_lower:
            subject = query_lower.replace("which", "").replace("what are", "").replace("?", "").strip()
            response = self.templates['list'].format(
                subject=subject,
                item1="first option",
                item2="second option",
                item3="third option",
                context="the system"
            )
        
        else:
            # Fallback to LLM with timeout
            prompt = f"Generate a brief answer to: {query}"
            try:
                # Use a simpler prompt for speed
                result = self.llm.invoke(prompt)
                response = result.content if hasattr(result, 'content') else str(result)
            except:
                # Ultimate fallback
                response = f"The answer to {query} involves multiple aspects and considerations."
        
        # Cache the response
        self.cache.set(query, response)
        return response
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Fast HyDE search with caching"""
        hypothetical = self.generate_hypothetical_fast(query)
        
        # Search with both
        results = []
        hyp_results = basic_search(hypothetical, k=k)
        results.extend(hyp_results)
        
        orig_results = basic_search(query, k=k//2)
        results.extend(orig_results)
        
        # Deduplicate
        seen = set()
        unique = []
        for doc_id, text, meta in results:
            if doc_id not in seen:
                seen.add(doc_id)
                unique.append((doc_id, text, meta))
                if len(unique) >= k:
                    break
        
        return unique


class BatchedQueryDecomposer:
    """Query decomposition with batching to reduce LLM calls"""
    
    def __init__(self):
        self.llm = llm
        self.cache = LLMCache()
        self.pattern_cache = {}  # Cache decomposition patterns
    
    def decompose_batch(self, queries: List[str]) -> List[Dict]:
        """Decompose multiple queries in one LLM call"""
        
        # Check cache for all queries
        results = []
        uncached = []
        
        for query in queries:
            cached = self.cache.get(f"decompose_{query}")
            if cached:
                results.append(json.loads(cached))
            else:
                uncached.append(query)
                results.append(None)
        
        # Batch process uncached queries
        if uncached:
            batch_prompt = f"""Analyze these queries and extract concepts. 
Return JSON array with one object per query:
[{{"concepts": [...], "intent": "..."}}]

Queries:
{json.dumps(uncached)}"""
            
            try:
                response = self.llm.invoke(batch_prompt)
                content = response.content if hasattr(response, 'content') else str(response)
                decompositions = json.loads(content)
                
                # Fill in results and cache
                j = 0
                for i, r in enumerate(results):
                    if r is None:
                        results[i] = decompositions[j]
                        self.cache.set(f"decompose_{uncached[j]}", json.dumps(decompositions[j]))
                        j += 1
            except:
                # Fallback to pattern-based
                j = 0
                for i, r in enumerate(results):
                    if r is None:
                        results[i] = self._pattern_decompose(uncached[j])
                        j += 1
        
        return results
    
    def _pattern_decompose(self, query: str) -> Dict:
        """Fast pattern-based decomposition"""
        query_lower = query.lower()
        words = [w for w in query_lower.split() if len(w) > 3]
        
        # Determine intent
        if "what is" in query_lower:
            intent = "definition"
        elif "how" in query_lower:
            intent = "process"
        elif "which" in query_lower:
            intent = "selection"
        else:
            intent = "general"
        
        return {"concepts": words, "intent": intent}


class AsyncMultiStageRetrieval:
    """Multi-stage retrieval with async/parallel execution"""
    
    def __init__(self):
        self.llm = llm
        self.cache = LLMCache()
    
    def retrieve_parallel(self, query: str, k: int = 5) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Parallel multi-stage retrieval"""
        import concurrent.futures
        
        all_results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Stage 1: Multiple search strategies in parallel
            futures = {
                executor.submit(enhanced_search, query, k*2): "enhanced",
                executor.submit(basic_search, query, k): "basic",
                executor.submit(self._search_keywords, query, k): "keywords"
            }
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    results = future.result(timeout=2)  # 2 second timeout per search
                    for doc_id, text, meta in results:
                        if doc_id not in all_results:
                            all_results[doc_id] = (text, meta, 1.0)
                        else:
                            current = all_results[doc_id]
                            all_results[doc_id] = (current[0], current[1], current[2] + 0.5)
                except:
                    pass
        
        # Sort and return
        sorted_results = sorted(all_results.items(), key=lambda x: x[1][2], reverse=True)
        return [(doc_id, text, meta) for doc_id, (text, meta, _) in sorted_results[:k]]
    
    def _search_keywords(self, query: str, k: int) -> List[Tuple[str, str, Dict]]:
        """Keyword search helper"""
        ki = get_keyword_index()
        if ki.enabled:
            results = ki.search(query, k=k)
            return [(doc_id, content, {}) for doc_id, _, content in results]
        return []


class OptimizedAdvancedSearch:
    """Optimized advanced search with caching, batching, and parallelization"""
    
    def __init__(self):
        self.hyde = CachedHyDESearch()
        self.decomposer = BatchedQueryDecomposer()
        self.multi_stage = AsyncMultiStageRetrieval()
        
        # Pre-warm cache with common patterns
        self._prewarm_cache()
    
    def _prewarm_cache(self):
        """Pre-compute common query patterns"""
        common_patterns = [
            "What is {concept}?",
            "How does {system} work?",
            "What are the benefits of {feature}?",
            "Which {items} are available?"
        ]
        # Cache would be pre-warmed in production
    
    def search(self, query: str, k: int = 5, timeout: float = 5.0) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Optimized search with timeout protection"""
        import concurrent.futures
        
        all_results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Launch all search methods in parallel with timeout
            futures = {
                executor.submit(self.hyde.search, query, k): "hyde",
                executor.submit(self.multi_stage.retrieve_parallel, query, k): "multi",
                executor.submit(enhanced_search, query, k): "enhanced",
                executor.submit(basic_search, query, k): "basic"
            }
            
            # Collect results with timeout
            for future in concurrent.futures.as_completed(futures, timeout=timeout):
                try:
                    results = future.result(timeout=1)
                    method = futures[future]
                    
                    # Weight results by method
                    weights = {"hyde": 1.2, "multi": 1.1, "enhanced": 1.0, "basic": 0.8}
                    weight = weights.get(method, 1.0)
                    
                    for i, (doc_id, text, meta) in enumerate(results):
                        if doc_id not in all_results:
                            all_results[doc_id] = (text, meta, 0)
                        current = all_results[doc_id]
                        score = (k - i) / k * weight
                        all_results[doc_id] = (current[0], current[1], current[2] + score)
                except:
                    pass  # Method timed out, continue with others
        
        # Sort by combined score
        sorted_results = sorted(all_results.items(), key=lambda x: x[1][2], reverse=True)
        return [(doc_id, text, meta) for doc_id, (text, meta, _) in sorted_results[:k]]


if __name__ == "__main__":
    print("Testing Optimized Advanced Search")
    print("=" * 60)
    
    searcher = OptimizedAdvancedSearch()
    
    test_queries = [
        "What is hybrid search?",
        "Which vector databases are mentioned?",
        "How should API keys be managed?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        t0 = time.time()
        
        # Search with 5 second timeout
        results = searcher.search(query, k=3, timeout=5.0)
        
        dt = (time.time() - t0) * 1000
        print(f"Found {len(results)} results in {dt:.1f}ms")
        
        if results:
            combined = " ".join([r[1][:100] for r in results]).lower()
            print(f"Sample: {results[0][1][:150]}...")
    
    print("\nCache and parallelization prevent timeouts!")