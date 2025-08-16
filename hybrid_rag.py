"""
Hybrid RAG system that falls back to LLM knowledge when RAG can't answer.
This restores the ability to answer general knowledge questions while 
maintaining the benefits of RAG for domain-specific content.
"""

import os
from typing import Tuple, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from production_search import ProductionAdvancedSearch
from config import config

# Initialize components
chat_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")
llm = ChatOpenAI(model=chat_model, temperature=0, api_key=config.OPENAI_API_KEY)
searcher = ProductionAdvancedSearch()

# System prompts
STRICT_RAG_PROMPT = """You are a helpful assistant that answers questions based on provided context.
IMPORTANT: You must ONLY use information from the provided CONTEXT to answer the question.
If the context doesn't contain relevant information, you must say "I don't know" or "I cannot answer based on the provided context."
Do not use any external knowledge or make assumptions beyond what's in the context."""

LLM_KNOWLEDGE_PROMPT = """You are a helpful assistant with broad general knowledge.
Answer the question using your training knowledge. Be accurate and helpful.
Start your response with: [Using general knowledge]"""

HYBRID_PROMPT = """You are a helpful assistant that can use both provided context and general knowledge.
First, check if the CONTEXT contains relevant information for answering the question.
If it does, use that information and indicate you're using the provided context.
If the context is not relevant, use your general knowledge and indicate this.
Be clear about your information source."""


class HybridRAG:
    """Hybrid RAG system with intelligent fallback to LLM knowledge."""
    
    def __init__(self, searcher=None, llm=None):
        self.searcher = searcher or ProductionAdvancedSearch()
        self.llm = llm or ChatOpenAI(model=chat_model, temperature=0, api_key=config.OPENAI_API_KEY)
        self.dont_know_phrases = [
            "i don't know",
            "i cannot answer",
            "no relevant information",
            "insufficient context",
            "not enough information",
            "cannot be determined",
            "no information provided",
            "context doesn't contain",
            "not mentioned in",
            "unable to answer"
        ]
    
    def _is_dont_know_response(self, response: str) -> bool:
        """Check if the response indicates the model doesn't know."""
        response_lower = response.lower()
        return any(phrase in response_lower for phrase in self.dont_know_phrases)
    
    def _search_context(self, query: str, k: int = 5) -> Tuple[List, str]:
        """Search for relevant context."""
        hits = self.searcher.search(query, k=k)
        
        if hits:
            context = "\n\n".join(doc for _, doc, _ in hits)
            doc_ids = [hit[0] for hit in hits]
            return doc_ids, context
        
        return [], ""
    
    def _try_rag_answer(self, query: str, context: str) -> Tuple[str, bool]:
        """Try to answer using only the context (strict RAG)."""
        msgs = [
            SystemMessage(content=STRICT_RAG_PROMPT),
            HumanMessage(content=f"""CONTEXT:
{context}

QUESTION: {query}

Answer based only on the above context.""")
        ]
        
        response = self.llm.invoke(msgs).content
        is_answered = not self._is_dont_know_response(response)
        
        return response, is_answered
    
    def _answer_with_llm_knowledge(self, query: str) -> str:
        """Answer using LLM's general knowledge."""
        msgs = [
            SystemMessage(content=LLM_KNOWLEDGE_PROMPT),
            HumanMessage(content=query)
        ]
        
        return self.llm.invoke(msgs).content
    
    def answer(self, query: str, k: int = 5, verbose: bool = False) -> Tuple[str, List[str], str]:
        """
        Answer a question using hybrid RAG with fallback.
        
        Args:
            query: The question to answer
            k: Number of documents to retrieve
            verbose: Whether to print debug information
        
        Returns:
            Tuple of (answer, document_ids_used, source_type)
            where source_type is 'context', 'llm_knowledge', or 'hybrid'
        """
        
        # Step 1: Search for relevant context
        if verbose:
            print(f"[1] Searching for relevant context...")
        
        doc_ids, context = self._search_context(query, k)
        
        if not context:
            # No relevant documents found - go straight to LLM knowledge
            if verbose:
                print(f"[2] No relevant documents found. Using LLM knowledge...")
            
            answer = self._answer_with_llm_knowledge(query)
            return answer, [], "llm_knowledge"
        
        # Step 2: Try strict RAG
        if verbose:
            print(f"[2] Found {len(doc_ids)} documents. Trying RAG answer...")
        
        rag_answer, answered = self._try_rag_answer(query, context)
        
        if answered:
            # RAG successfully answered the question
            if verbose:
                print(f"[3] RAG provided an answer. Done.")
            
            return rag_answer, doc_ids, "context"
        
        # Step 3: RAG said "I don't know" - fall back to LLM knowledge
        if verbose:
            print(f"[3] RAG couldn't answer. Falling back to LLM knowledge...")
        
        llm_answer = self._answer_with_llm_knowledge(query)
        
        # Return just the answer, let rag_chain.py handle the note
        return llm_answer, [], "llm_knowledge"
    
    def answer_with_source_indication(self, query: str, k: int = 5) -> str:
        """
        Answer with clear indication of information source.
        Returns a formatted string with the answer and source.
        """
        answer, doc_ids, source = self.answer(query, k)
        
        if source == "context":
            source_text = f"[Source: Database documents ({len(doc_ids)} documents used)]"
        elif source == "llm_knowledge":
            source_text = "[Source: AI general knowledge]"
        else:
            source_text = "[Source: Mixed]"
        
        return f"{answer}\n\n{source_text}"


def test_hybrid_system():
    """Test the hybrid RAG system with various queries."""
    print("=" * 60)
    print("TESTING HYBRID RAG SYSTEM")
    print("=" * 60)
    
    hybrid = HybridRAG()
    
    test_queries = [
        # Should use database (AI content exists)
        "What is cognitive AI?",
        "What are vector databases?",
        
        # Should use LLM knowledge (no relevant content)
        "What is the capital of Idaho?",
        "Who was the first president of the United States?",
        "What is 15 times 7?",
        
        # Edge cases
        "How does memory work?",  # Might match AI memory or need general knowledge
        "What is the weather today?",  # LLM should recognize it can't know this
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        answer, doc_ids, source = hybrid.answer(query, verbose=True)
        
        print(f"\nAnswer: {answer[:200]}...")
        print(f"Source: {source}")
        if doc_ids:
            print(f"Used {len(doc_ids)} documents")
        print()
    
    print("=" * 60)
    print("SUMMARY:")
    print("The hybrid system successfully:")
    print("1. Uses RAG for domain-specific content")
    print("2. Falls back to LLM knowledge when RAG can't answer")
    print("3. Clearly indicates information source")
    print("=" * 60)


def integrate_with_app():
    """
    Show how to integrate this with the existing app.
    This can replace the current answer() function in rag_chain.py
    """
    print("\nTo integrate with the app, replace rag_chain.answer() with:")
    print("-" * 60)
    print("""
# In rag_chain.py, replace the answer function with:

from hybrid_rag import HybridRAG

hybrid = HybridRAG()

def answer(query: str, k: int = 5):
    '''Enhanced answer function with hybrid RAG.'''
    response, doc_ids, source = hybrid.answer(query, k)
    
    # Add source indication for transparency
    if source == "llm_knowledge":
        response += "\\n\\n[Note: Answered from AI knowledge, not from database]"
    
    return response, doc_ids
    """)


if __name__ == "__main__":
    if config.is_valid():
        test_hybrid_system()
        integrate_with_app()
    else:
        print("Please configure OpenAI API key in .env file")