"""
Hybrid answering system that combines:
1. RAG search for domain-specific content
2. LLM's built-in knowledge for general facts
"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from search_enhancements import search
from config import config

chat_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")
llm = ChatOpenAI(model=chat_model, temperature=0, api_key=config.OPENAI_API_KEY)


def hybrid_answer(query: str, k: int = 5, use_llm_knowledge: bool = True):
    """
    Answer using both retrieved context AND LLM's knowledge.
    
    Args:
        query: The question to answer
        k: Number of documents to retrieve
        use_llm_knowledge: Whether to allow LLM to use its training knowledge
    """
    
    # Step 1: Try to find relevant context
    hits = search(query, k)
    
    if hits:
        # We have relevant context
        ctx = "\n\n".join(doc for _, doc, *_ in hits)
        
        if use_llm_knowledge:
            # HYBRID: Use context + LLM knowledge
            system_prompt = """You are a helpful assistant. 
            First, check if the provided CONTEXT contains relevant information.
            If it does, prioritize that information in your answer.
            If the context is not relevant or insufficient, you may use your general knowledge.
            Always indicate whether you're using the provided context or your general knowledge."""
            
            user_prompt = f"""CONTEXT (from database):
{ctx}

QUESTION: {query}

Please answer the question. If the context is relevant, use it. Otherwise, use your knowledge."""
        else:
            # STRICT RAG: Only use context
            system_prompt = "You ground answers ONLY in CONTEXT. If insufficient, say you don't know."
            user_prompt = f"CONTEXT:\n{ctx}\n\nQUESTION: {query}"
    
    else:
        # No relevant context found
        if use_llm_knowledge:
            # Fall back to pure LLM
            system_prompt = """You are a helpful assistant. 
            No relevant context was found in the database for this question.
            Please answer using your general knowledge, and mention that this is from your training data."""
            user_prompt = query
        else:
            # Strict mode - can't answer without context
            return "No relevant information found in the database.", []
    
    # Get response
    msgs = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    response = llm.invoke(msgs).content
    used_ids = [h[0] for h in hits] if hits else []
    
    return response, used_ids


def smart_answer(query: str, k: int = 5):
    """
    Intelligently decide whether to use RAG or LLM knowledge based on the query.
    """
    
    # First, check if we have relevant content
    hits = search(query, k)
    
    if hits:
        # Calculate relevance score
        ctx = " ".join(doc for _, doc, *_ in hits).lower()
        query_words = query.lower().split()
        
        # Simple relevance: how many query words appear in context
        relevance = sum(1 for word in query_words if word in ctx) / len(query_words)
        
        if relevance > 0.5:
            # High relevance - use RAG strictly
            print(f"[Using RAG - relevance: {relevance:.2f}]")
            return answer_with_rag(query, hits)
        else:
            # Low relevance - use hybrid
            print(f"[Using Hybrid - relevance: {relevance:.2f}]")
            return hybrid_answer(query, k, use_llm_knowledge=True)
    else:
        # No hits - use pure LLM
        print("[Using LLM knowledge - no relevant documents]")
        return answer_with_llm(query)


def answer_with_rag(query: str, hits: list):
    """Pure RAG answer using only context."""
    ctx = "\n\n".join(doc for _, doc, *_ in hits)
    
    msgs = [
        SystemMessage(content="Answer ONLY using the provided context. Be specific and accurate."),
        HumanMessage(content=f"CONTEXT:\n{ctx}\n\nQUESTION: {query}")
    ]
    
    response = llm.invoke(msgs).content
    return response, [h[0] for h in hits]


def answer_with_llm(query: str):
    """Pure LLM answer using training knowledge."""
    msgs = [
        SystemMessage(content="Answer using your knowledge. Be helpful and accurate."),
        HumanMessage(content=query)
    ]
    
    response = llm.invoke(msgs).content
    return response + "\n\n[Note: Answered from AI's general knowledge, not from database]", []


def test_hybrid_system():
    """Test the hybrid answering system."""
    
    test_queries = [
        # Should use database (AI content exists)
        "What is cognitive AI?",
        "How do vector databases work?",
        
        # Should use LLM knowledge (no relevant content)
        "What is the capital of Idaho?",
        "Who wrote Romeo and Juliet?",
        "What is 2+2?",
        
        # Mixed - might use hybrid
        "How does memory work?",  # Could match AI memory or general memory
    ]
    
    print("TESTING HYBRID ANSWERING SYSTEM")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        response, used_ids = smart_answer(query)
        
        print(f"Response: {response[:200]}...")
        if used_ids:
            print(f"Used {len(used_ids)} documents from database")
        else:
            print("No documents used - pure LLM response")
    
    print("\n" + "=" * 60)
    print("The hybrid system can answer BOTH:")
    print("1. Domain-specific questions (from database)")
    print("2. General knowledge questions (from LLM training)")


if __name__ == "__main__":
    # Only run test if API key is configured
    if config.is_valid():
        test_hybrid_system()
    else:
        print("Configure OpenAI API key to test hybrid system")