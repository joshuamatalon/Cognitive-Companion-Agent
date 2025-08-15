"""
Advanced search methods: HyDE, Cross-encoder, Multi-stage, Query Decomposition
These are novel solutions to improve recall without cherry-picking.
"""

import os
import json
import time
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

# Import existing search functions
from vec_memory import search as basic_search
from keyword_search import get_keyword_index
from search_enhancements import enhanced_search
from rag_chain import llm

# Try to import sentence transformers for cross-encoder
try:
    from sentence_transformers import CrossEncoder
    HAS_CROSS_ENCODER = True
except ImportError:
    HAS_CROSS_ENCODER = False
    print("Warning: sentence-transformers not installed. Cross-encoder disabled.")


@dataclass
class QueryDecomposition:
    """Structured query understanding"""
    intent: str  # definition, comparison, procedure, factual, analytical
    main_concepts: List[str]
    related_terms: List[str]
    answer_pattern: str
    search_strategy: str


class HyDESearch:
    """Hypothetical Document Embeddings - generate ideal answers then search"""
    
    def __init__(self):
        self.llm = llm
    
    def generate_hypothetical_answer(self, query: str) -> str:
        """Generate a hypothetical perfect answer to the query"""
        prompt = f"""Generate a comprehensive, factual answer to this question. 
        Be specific and include relevant details that would be found in documentation.
        
        Question: {query}
        
        Comprehensive Answer:"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"HyDE generation failed: {e}")
            # Fallback to simple expansion
            return f"{query}. The answer involves {query.replace('?', '').replace('What is', '').replace('How', '')}"
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Search using hypothetical document embeddings"""
        # Generate hypothetical answer
        hypothetical = self.generate_hypothetical_answer(query)
        
        # Search for chunks similar to the hypothetical answer
        # Use both the hypothetical and original query
        results = []
        
        # Search with hypothetical answer
        hyp_results = basic_search(hypothetical, k=k*2)
        results.extend(hyp_results)
        
        # Also search with original query for diversity
        orig_results = basic_search(query, k=k)
        results.extend(orig_results)
        
        # Deduplicate
        seen = set()
        unique_results = []
        for doc_id, text, meta in results:
            if doc_id not in seen:
                seen.add(doc_id)
                unique_results.append((doc_id, text, meta))
                if len(unique_results) >= k:
                    break
        
        return unique_results


class CrossEncoderReranker:
    """Cross-encoder for more accurate query-document matching"""
    
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        self.enabled = HAS_CROSS_ENCODER
        if self.enabled:
            try:
                self.model = CrossEncoder(model_name)
            except Exception as e:
                print(f"Failed to load cross-encoder: {e}")
                self.enabled = False
        else:
            self.model = None
    
    def rerank(self, query: str, documents: List[Tuple[str, str, Dict]], k: int = 5) -> List[Tuple[str, str, Dict, float]]:
        """Re-rank documents using cross-encoder"""
        if not self.enabled or not documents:
            # Fallback: return documents with simple scoring
            return [(d[0], d[1], d[2], 1.0) for d in documents[:k]]
        
        # Prepare pairs for cross-encoder
        pairs = [(query, doc[1]) for doc in documents]
        
        try:
            # Get cross-encoder scores
            scores = self.model.predict(pairs)
            
            # Combine with documents and sort
            scored_docs = [
                (documents[i][0], documents[i][1], documents[i][2], float(scores[i]))
                for i in range(len(documents))
            ]
            scored_docs.sort(key=lambda x: x[3], reverse=True)
            
            return scored_docs[:k]
        except Exception as e:
            print(f"Cross-encoder reranking failed: {e}")
            return [(d[0], d[1], d[2], 1.0) for d in documents[:k]]


class MultiStageRetrieval:
    """Multi-stage retrieval with reasoning about what's missing"""
    
    def __init__(self):
        self.llm = llm
        self.hyde = HyDESearch()
    
    def analyze_gaps(self, query: str, initial_results: List[Tuple[str, str, Dict]]) -> str:
        """Analyze what information is missing from initial results"""
        if not initial_results:
            return query
        
        context = "\n".join([doc[1][:200] for doc in initial_results[:3]])
        
        prompt = f"""Given this query and initial search results, identify what key information is missing.

Query: {query}

Initial results:
{context}

What specific information is needed to fully answer the query but is missing from these results?
Be concise and specific:"""
        
        try:
            response = self.llm.invoke(prompt)
            missing = response.content if hasattr(response, 'content') else str(response)
            return missing.strip()
        except:
            # Fallback: try different search terms
            return query.replace("What is", "definition of").replace("How", "steps to")
    
    def retrieve(self, query: str, k: int = 5) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Multi-stage retrieval process"""
        all_results = {}
        
        # Stage 1: Broad initial search
        stage1_results = enhanced_search(query, k=k*3)
        for doc_id, text, meta in stage1_results:
            if doc_id not in all_results:
                all_results[doc_id] = (text, meta, 1.0)  # stage 1 weight
        
        # Stage 2: Analyze what's missing
        missing_info = self.analyze_gaps(query, stage1_results)
        
        # Stage 3: Targeted search for missing information
        if missing_info and missing_info != query:
            stage3_results = basic_search(missing_info, k=k)
            for doc_id, text, meta in stage3_results:
                if doc_id not in all_results:
                    all_results[doc_id] = (text, meta, 0.8)  # stage 3 weight
                else:
                    # Boost score if found in both stages
                    current = all_results[doc_id]
                    all_results[doc_id] = (current[0], current[1], current[2] + 0.5)
        
        # Stage 4: HyDE search for comprehensive coverage
        hyde_results = self.hyde.search(query, k=k)
        for doc_id, text, meta in hyde_results:
            if doc_id not in all_results:
                all_results[doc_id] = (text, meta, 0.7)  # hyde weight
            else:
                current = all_results[doc_id]
                all_results[doc_id] = (current[0], current[1], current[2] + 0.3)
        
        # Sort by combined score and return top k
        sorted_results = sorted(all_results.items(), key=lambda x: x[1][2], reverse=True)
        return [(doc_id, text, meta) for doc_id, (text, meta, _) in sorted_results[:k]]


class QueryDecomposer:
    """Decompose queries to understand intent and required information"""
    
    def __init__(self):
        self.llm = llm
        self.intent_patterns = {
            'definition': ['what is', 'what are', 'define'],
            'comparison': ['vs', 'versus', 'difference', 'compare'],
            'procedure': ['how to', 'how do', 'how should', 'steps'],
            'factual': ['which', 'when', 'where', 'who', 'percentage', 'number'],
            'analytical': ['why', 'explain', 'analyze', 'understand']
        }
    
    def decompose(self, query: str) -> QueryDecomposition:
        """Decompose query into structured understanding"""
        query_lower = query.lower()
        
        # Determine intent
        intent = 'general'
        for intent_type, patterns in self.intent_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                intent = intent_type
                break
        
        # Use LLM for sophisticated decomposition
        prompt = f"""Analyze this query and extract:
1. Main concepts (key nouns/topics)
2. Related terms that might help find answers
3. The type of answer expected

Query: {query}

Provide response in JSON format:
{{
  "main_concepts": [...],
  "related_terms": [...],
  "answer_pattern": "..."
}}"""
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                main_concepts = data.get('main_concepts', [])
                related_terms = data.get('related_terms', [])
                answer_pattern = data.get('answer_pattern', '')
            else:
                raise ValueError("No JSON found")
                
        except Exception as e:
            # Fallback to simple extraction
            words = query_lower.replace('?', '').split()
            main_concepts = [w for w in words if len(w) > 3 and w not in ['what', 'how', 'when', 'where', 'which']]
            related_terms = []
            answer_pattern = f"{query.replace('?', '')} is"
        
        # Determine search strategy based on intent
        if intent == 'definition':
            search_strategy = 'focus_on_is_statements'
        elif intent == 'comparison':
            search_strategy = 'find_contrasts'
        elif intent == 'procedure':
            search_strategy = 'find_steps_and_processes'
        elif intent == 'factual':
            search_strategy = 'find_specific_facts'
        else:
            search_strategy = 'broad_search'
        
        return QueryDecomposition(
            intent=intent,
            main_concepts=main_concepts,
            related_terms=related_terms,
            answer_pattern=answer_pattern,
            search_strategy=search_strategy
        )
    
    def search_with_decomposition(self, query: str, k: int = 5) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Search using query decomposition insights"""
        decomp = self.decompose(query)
        
        all_results = {}
        
        # Search for main concepts
        for concept in decomp.main_concepts[:3]:
            results = basic_search(concept, k=3)
            for doc_id, text, meta in results:
                if doc_id not in all_results:
                    all_results[doc_id] = (text, meta, 1.0)
        
        # Search for related terms
        for term in decomp.related_terms[:2]:
            results = basic_search(term, k=2)
            for doc_id, text, meta in results:
                if doc_id not in all_results:
                    all_results[doc_id] = (text, meta, 0.7)
        
        # Search with answer pattern
        if decomp.answer_pattern:
            results = basic_search(decomp.answer_pattern, k=3)
            for doc_id, text, meta in results:
                if doc_id not in all_results:
                    all_results[doc_id] = (text, meta, 0.8)
                else:
                    # Boost if found multiple times
                    current = all_results[doc_id]
                    all_results[doc_id] = (current[0], current[1], current[2] + 0.5)
        
        # Apply intent-specific boosting
        sorted_results = []
        for doc_id, (text, meta, score) in all_results.items():
            # Boost based on intent matching
            if decomp.intent == 'definition' and ' is ' in text.lower():
                score += 0.5
            elif decomp.intent == 'factual' and any(c.isdigit() for c in text):
                score += 0.3
            elif decomp.intent == 'procedure' and any(word in text.lower() for word in ['step', 'first', 'then', 'next']):
                score += 0.4
            
            sorted_results.append((doc_id, text, meta, score))
        
        # Sort by score
        sorted_results.sort(key=lambda x: x[3], reverse=True)
        
        return [(doc_id, text, meta) for doc_id, text, meta, _ in sorted_results[:k]]


class UnifiedAdvancedSearch:
    """Combines all 4 advanced search methods"""
    
    def __init__(self):
        print("Initializing advanced search components...")
        self.hyde = HyDESearch()
        self.cross_encoder = CrossEncoderReranker()
        self.multi_stage = MultiStageRetrieval()
        self.decomposer = QueryDecomposer()
        print("Advanced search ready.")
    
    def search(self, query: str, k: int = 5, method: str = 'all') -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Unified search using all or specific advanced methods.
        
        Args:
            query: Search query
            k: Number of results
            method: 'all', 'hyde', 'cross_encoder', 'multi_stage', 'decompose'
        """
        
        if method == 'hyde':
            return self.hyde.search(query, k)
        
        elif method == 'decompose':
            return self.decomposer.search_with_decomposition(query, k)
        
        elif method == 'multi_stage':
            return self.multi_stage.retrieve(query, k)
        
        elif method == 'cross_encoder':
            # Get candidates and rerank
            candidates = enhanced_search(query, k=k*5)
            reranked = self.cross_encoder.rerank(query, candidates, k)
            return [(d[0], d[1], d[2]) for d in reranked]
        
        else:  # method == 'all'
            # Combine all methods
            all_results = {}
            weights = {}
            
            # 1. HyDE search
            hyde_results = self.hyde.search(query, k=k*2)
            for i, (doc_id, text, meta) in enumerate(hyde_results):
                if doc_id not in all_results:
                    all_results[doc_id] = (text, meta)
                    weights[doc_id] = 0
                weights[doc_id] += (k*2 - i) / (k*2) * 1.0  # HyDE weight
            
            # 2. Query decomposition search
            decomp_results = self.decomposer.search_with_decomposition(query, k=k*2)
            for i, (doc_id, text, meta) in enumerate(decomp_results):
                if doc_id not in all_results:
                    all_results[doc_id] = (text, meta)
                    weights[doc_id] = 0
                weights[doc_id] += (k*2 - i) / (k*2) * 0.9  # Decomposition weight
            
            # 3. Multi-stage retrieval
            multi_results = self.multi_stage.retrieve(query, k=k*2)
            for i, (doc_id, text, meta) in enumerate(multi_results):
                if doc_id not in all_results:
                    all_results[doc_id] = (text, meta)
                    weights[doc_id] = 0
                weights[doc_id] += (k*2 - i) / (k*2) * 1.1  # Multi-stage weight
            
            # 4. Use cross-encoder to rerank the combined results
            combined = [(doc_id, text, meta) for doc_id, (text, meta) in all_results.items()]
            
            # Sort by initial weights to get top candidates
            combined_weighted = [(doc_id, text, meta, weights.get(doc_id, 0)) 
                                for doc_id, (text, meta) in all_results.items()]
            combined_weighted.sort(key=lambda x: x[3], reverse=True)
            
            # Rerank top candidates with cross-encoder
            top_candidates = [(d[0], d[1], d[2]) for d in combined_weighted[:k*3]]
            final_ranked = self.cross_encoder.rerank(query, top_candidates, k)
            
            return [(d[0], d[1], d[2]) for d in final_ranked]


def test_advanced_search():
    """Test the advanced search methods on challenging queries"""
    
    print("Testing Advanced Search Methods")
    print("=" * 60)
    
    searcher = UnifiedAdvancedSearch()
    
    # Test queries that previously failed
    test_queries = [
        "What is hybrid search?",
        "Which vector databases are mentioned for cognitive AI?",
        "How should API keys be managed?",
        "What benefits does healthcare see from cognitive AI?",
        "How does cognitive AI transform education?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        # Test each method
        methods = ['hyde', 'decompose', 'multi_stage', 'all']
        for method in methods:
            results = searcher.search(query, k=3, method=method)
            if results:
                print(f"{method.upper()}: Found {len(results)} results")
                # Check if key terms are in results
                combined = " ".join([r[1][:100] for r in results]).lower()
                if "hybrid" in query.lower() and "semantic" in combined and "keyword" in combined:
                    print("  -> Contains hybrid search info [OK]")
                elif "vector database" in query.lower() and ("pinecone" in combined or "weaviate" in combined):
                    print("  -> Contains vector database info [OK]")
                elif "api key" in query.lower() and "never expose" in combined:
                    print("  -> Contains API key info [OK]")
            else:
                print(f"{method.upper()}: No results")


if __name__ == "__main__":
    test_advanced_search()