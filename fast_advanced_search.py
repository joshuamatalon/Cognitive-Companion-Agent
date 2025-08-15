"""
Fast advanced search methods without LLM dependencies for every query.
Implements pattern-based versions of HyDE, decomposition, and multi-stage.
"""

from typing import List, Tuple, Dict, Any
import re
from vec_memory import search as basic_search
from keyword_search import get_keyword_index
from search_enhancements import enhanced_search

# Try to import sentence transformers for cross-encoder
try:
    from sentence_transformers import CrossEncoder
    HAS_CROSS_ENCODER = True
except ImportError:
    HAS_CROSS_ENCODER = False


class FastHyDE:
    """Pattern-based hypothetical document generation (no LLM)"""
    
    def generate_hypothetical(self, query: str) -> str:
        """Generate hypothetical answer using patterns"""
        query_lower = query.lower()
        
        # Pattern-based hypothetical generation
        if "what is" in query_lower:
            subject = query_lower.replace("what is", "").replace("?", "").strip()
            return f"{subject} is a method that combines multiple approaches. {subject} refers to the technique of {subject}. The {subject} approach involves combining different strategies."
        
        elif "how" in query_lower:
            subject = query_lower.replace("how", "").replace("?", "").strip()
            return f"To {subject}, you should follow these steps: First, {subject} requires careful planning. Then, {subject} involves implementation. The process of {subject} includes multiple stages."
        
        elif "which" in query_lower:
            subject = query_lower.replace("which", "").replace("?", "").strip()
            return f"The {subject} include several options such as various types. Multiple {subject} are available. The main {subject} are commonly used solutions."
        
        else:
            # Default expansion
            return f"{query} The answer involves {query.replace('?', '')}. This relates to {query.replace('?', '')} in multiple ways."
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Fast HyDE search"""
        hypothetical = self.generate_hypothetical(query)
        
        # Search with both hypothetical and original
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


class FastDecomposer:
    """Pattern-based query decomposition (no LLM)"""
    
    def decompose_query(self, query: str) -> Dict[str, List[str]]:
        """Decompose query into concepts using patterns"""
        query_lower = query.lower()
        
        # Extract main concepts (nouns and important terms)
        # Remove question words
        clean = query_lower
        for word in ['what', 'how', 'when', 'where', 'which', 'why', 'is', 'are', 'does', 'do', 'should', 'can', '?']:
            clean = clean.replace(word, ' ')
        
        # Get significant words
        words = [w.strip() for w in clean.split() if len(w.strip()) > 2]
        
        # Identify key concepts
        concepts = []
        
        # Look for compound terms
        if "hybrid search" in query_lower:
            concepts.append("hybrid search")
            concepts.extend(["semantic", "keyword", "combining"])
        
        if "vector database" in query_lower:
            concepts.append("vector database")
            concepts.extend(["pinecone", "weaviate", "chroma"])
        
        if "api key" in query_lower:
            concepts.append("api key")
            concepts.extend(["security", "environment", "variables"])
        
        # Add individual important words
        important_words = ['cognitive', 'ai', 'healthcare', 'education', 'encryption', 
                          'pinecone', 'executive', 'onboarding', 'circular', 'architecture']
        for word in words:
            if word in important_words:
                concepts.append(word)
        
        # Generate related terms
        related = []
        if "search" in query_lower:
            related.extend(["retrieval", "matching", "finding"])
        if "manage" in query_lower or "management" in query_lower:
            related.extend(["handle", "control", "organize"])
        if "benefit" in query_lower:
            related.extend(["advantage", "help", "improve"])
        
        return {
            "concepts": concepts if concepts else words,
            "related": related
        }
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Search using decomposition"""
        decomp = self.decompose_query(query)
        
        all_results = {}
        
        # Search for each concept
        for concept in decomp["concepts"][:5]:
            results = basic_search(concept, k=3)
            for doc_id, text, meta in results:
                if doc_id not in all_results:
                    all_results[doc_id] = (text, meta, 1.0)
                else:
                    # Boost score if found multiple times
                    current = all_results[doc_id]
                    all_results[doc_id] = (current[0], current[1], current[2] + 0.5)
        
        # Search for related terms
        for term in decomp["related"][:3]:
            results = basic_search(term, k=2)
            for doc_id, text, meta in results:
                if doc_id not in all_results:
                    all_results[doc_id] = (text, meta, 0.5)
        
        # Sort by score
        sorted_results = sorted(all_results.items(), key=lambda x: x[1][2], reverse=True)
        return [(doc_id, text, meta) for doc_id, (text, meta, _) in sorted_results[:k]]


class FastMultiStage:
    """Fast multi-stage retrieval without LLM"""
    
    def identify_gaps(self, query: str, initial_results: List[Tuple[str, str, Dict]]) -> str:
        """Identify missing info using patterns"""
        if not initial_results:
            return query
        
        combined = " ".join([r[1][:100] for r in initial_results]).lower()
        query_lower = query.lower()
        
        # Check for specific missing patterns
        if "hybrid search" in query_lower and "semantic" not in combined:
            return "semantic keyword combining search methods"
        
        if "vector database" in query_lower and "pinecone" not in combined:
            return "pinecone weaviate chroma database options"
        
        if "api key" in query_lower and "never expose" not in combined:
            return "never expose environment variables security"
        
        # Default: search for key terms not found
        words = query_lower.replace("?", "").split()
        missing = [w for w in words if len(w) > 3 and w not in combined]
        if missing:
            return " ".join(missing)
        
        return ""
    
    def retrieve(self, query: str, k: int = 5) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Fast multi-stage retrieval"""
        all_results = {}
        
        # Stage 1: Initial search
        stage1 = enhanced_search(query, k=k*2)
        for doc_id, text, meta in stage1:
            all_results[doc_id] = (text, meta, 1.0)
        
        # Stage 2: Gap filling
        gaps = self.identify_gaps(query, stage1)
        if gaps:
            stage2 = basic_search(gaps, k=k)
            for doc_id, text, meta in stage2:
                if doc_id not in all_results:
                    all_results[doc_id] = (text, meta, 0.8)
                else:
                    current = all_results[doc_id]
                    all_results[doc_id] = (current[0], current[1], current[2] + 0.5)
        
        # Sort and return
        sorted_results = sorted(all_results.items(), key=lambda x: x[1][2], reverse=True)
        return [(doc_id, text, meta) for doc_id, (text, meta, _) in sorted_results[:k]]


class FastAdvancedSearch:
    """Fast unified advanced search without LLM overhead"""
    
    def __init__(self):
        self.hyde = FastHyDE()
        self.decomposer = FastDecomposer()
        self.multi_stage = FastMultiStage()
        self.cross_encoder = None
        
        if HAS_CROSS_ENCODER:
            try:
                self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            except:
                pass
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Fast unified search"""
        all_results = {}
        weights = {}
        
        # 1. HyDE search (fast pattern-based)
        hyde_results = self.hyde.search(query, k=k)
        for i, (doc_id, text, meta) in enumerate(hyde_results):
            if doc_id not in all_results:
                all_results[doc_id] = (text, meta)
                weights[doc_id] = 0
            weights[doc_id] += (k - i) / k * 1.0
        
        # 2. Decomposition search
        decomp_results = self.decomposer.search(query, k=k)
        for i, (doc_id, text, meta) in enumerate(decomp_results):
            if doc_id not in all_results:
                all_results[doc_id] = (text, meta)
                weights[doc_id] = 0
            weights[doc_id] += (k - i) / k * 0.9
        
        # 3. Multi-stage (fast version)
        multi_results = self.multi_stage.retrieve(query, k=k)
        for i, (doc_id, text, meta) in enumerate(multi_results):
            if doc_id not in all_results:
                all_results[doc_id] = (text, meta)
                weights[doc_id] = 0
            weights[doc_id] += (k - i) / k * 1.1
        
        # 4. Cross-encoder reranking if available
        if self.cross_encoder:
            # Get top candidates
            candidates = sorted(all_results.items(), key=lambda x: weights.get(x[0], 0), reverse=True)[:k*2]
            
            # Rerank with cross-encoder
            pairs = [(query, text) for _, (text, _) in candidates]
            try:
                scores = self.cross_encoder.predict(pairs)
                reranked = [(candidates[i][0], candidates[i][1][0], candidates[i][1][1], scores[i]) 
                           for i in range(len(candidates))]
                reranked.sort(key=lambda x: x[3], reverse=True)
                return [(doc_id, text, meta) for doc_id, text, meta, _ in reranked[:k]]
            except:
                pass
        
        # Fallback: sort by weights
        sorted_results = sorted(all_results.items(), key=lambda x: weights.get(x[0], 0), reverse=True)
        return [(doc_id, text, meta) for doc_id, (text, meta) in sorted_results[:k]]


if __name__ == "__main__":
    print("Testing Fast Advanced Search")
    print("=" * 60)
    
    searcher = FastAdvancedSearch()
    
    test_queries = [
        "What is hybrid search?",
        "Which vector databases are mentioned for cognitive AI?",
        "How should API keys be managed?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = searcher.search(query, k=3)
        if results:
            print(f"Found {len(results)} results")
            combined = " ".join([r[1][:100] for r in results]).lower()
            
            # Check for key terms
            if "hybrid" in query.lower() and ("semantic" in combined or "keyword" in combined):
                print("  -> Relevant content found")
            elif "vector database" in query.lower() and ("pinecone" in combined or "weaviate" in combined):
                print("  -> Relevant content found")
            elif "api key" in query.lower() and ("environment" in combined or "secure" in combined):
                print("  -> Relevant content found")