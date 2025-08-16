import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from memory_backend import upsert_note
from hybrid_rag import HybridRAG
from config import config

# Check if API key is valid
if not config.is_valid():
    raise RuntimeError("Invalid configuration. Please check your API keys in .env file.")

chat_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")
llm = ChatOpenAI(model=chat_model, temperature=0, api_key=config.OPENAI_API_KEY)

# Initialize hybrid RAG system
hybrid = HybridRAG()

def answer(query: str, k: int = 5):
    """Enhanced answer function with hybrid RAG."""
    response, doc_ids, source = hybrid.answer(query, k)
    
    # Add source indication for transparency
    if source == "llm_knowledge":
        response += "\n\n[Note: Answered from AI knowledge, not from database]"
    
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
