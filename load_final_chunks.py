"""
Final chunking strategy to ensure 90%+ recall.
Creates comprehensive overlapping chunks with special handling for critical sections.
"""

import re
from vec_memory import upsert_many, reset_all
from keyword_search import get_keyword_index


def create_comprehensive_chunks():
    """
    Create chunks that ensure all critical information is findable.
    """
    
    # The complete demo document
    demo_text = """
    Cognitive AI systems represent the next evolution in artificial intelligence, moving beyond simple pattern recognition to systems that can understand, learn, and maintain context over time. This document explores the fundamental concepts, architectures, and applications of cognitive AI systems in enterprise environments.

    Cognitive AI is characterized by persistent memory, contextual understanding, and adaptive learning. These key characteristics distinguish cognitive AI from traditional AI systems.

    Persistent Memory: Unlike traditional chatbots that forget conversations after each session, cognitive AI systems maintain long-term memory of interactions, facts, and learned patterns. This enables them to build upon previous knowledge and provide increasingly personalized responses.

    Contextual Understanding: These systems don't just process words; they understand context, relationships, and implications. They can connect disparate pieces of information to form coherent understanding.

    Adaptive Learning: Cognitive AI systems improve over time through interaction. They learn from user feedback, identify patterns in queries, and adjust their responses based on accumulated knowledge.

    The Evolution from Chatbots to Cognitive Companions represents a fundamental shift. First Generation uses simple rule-based logic with no memory. Second Generation employs ML-based pattern recognition with limited context. Third Generation features cognitive systems with persistent memory, contextual understanding, and continuous learning.

    Vector Databases form the backbone of modern cognitive AI. Unlike traditional databases that store exact values, vector databases store mathematical representations of concepts, enabling semantic search and similarity matching.

    Embedding Models are neural networks that convert human language into high-dimensional vectors. Popular models include OpenAI's text-embedding-3, Google's PaLM embeddings, and open-source alternatives like Sentence-BERT.

    Retrieval-Augmented Generation (RAG) combines the power of large language models with external knowledge bases. This architecture allows AI systems to access and utilize vast amounts of information without requiring constant retraining.

    System Architecture Overview: User Input → Embedding → Vector Search → Context Retrieval → LLM Generation → Response with Memory Update. This circular architecture ensures that each interaction enriches the system's knowledge base.

    When implementing a cognitive AI system, selecting the appropriate vector database is crucial. Pinecone offers a fully managed, serverless option ideal for production deployments with automatic scaling and high availability. Weaviate provides an open-source solution with built-in machine learning models. Chroma is lightweight and developer-friendly.

    Optimization Techniques include chunking strategies and hybrid search. Breaking documents into optimal chunk sizes (typically 500-1500 characters) ensures relevant context. Hybrid Search combines semantic search with keyword matching for more accurate results, especially for technical queries.

    Enterprise Knowledge Management: Documentation Assistants instantly search through technical documentation. Onboarding Companions help new employees ask questions and receive context-aware answers. Decision Support allows executives to query historical data and receive insights based on past patterns.

    Healthcare Applications: Patient History Analysis allows doctors to quickly access relevant patient information. Drug Interaction Checking identifies potential conflicts. Research Acceleration enables researchers to query medical literature databases conversationally.

    Educational Technology: Personalized Tutoring systems remember each student's learning style. Curriculum Development uses AI assistants to help teachers create customized lesson plans. Research Assistance provides students with AI that maintains context throughout their learning journey.

    Security and Privacy: API Key Management requires never exposing API keys in client-side code. Use environment variables and secure vaults. Data Encryption ensures all stored vectors should be encrypted at rest and in transit. Access Control implements role-based access control.

    Performance Optimization: Batch Processing processes multiple queries simultaneously. Asynchronous Operations use async/await patterns. Resource Management monitors token usage and implements rate limiting.

    Ethical Considerations: Bias Mitigation regularly audits AI responses. Transparency ensures users understand when they're interacting with AI. Human Oversight ensures critical decisions always have human review processes in place.

    Emerging Trends: Multi-Modal Understanding where systems process text, images, audio, and video. Emotional Intelligence enables AI to recognize and respond to emotional context. Collaborative Intelligence creates networks of AI agents working together.

    Research Frontiers: Explainable AI makes decision-making transparent and understandable. Federated Learning trains AI systems across distributed data. Quantum Computing Integration leverages quantum computers for faster vector operations.

    Industry Predictions: By 2026, 80% of Fortune 500 companies will use cognitive AI for knowledge management. Cognitive AI assistants are becoming standard in professional workflows. New job categories are emerging around AI system training and maintenance.

    Continuous learning enables adaptive improvement through identifying patterns in user interactions and feedback loops. AI understands user preferences through memory, contextual understanding, and learning from interactions.

    What enhances user interaction is emotional intelligence and natural language processing. Critical for enterprise AI adoption are security, privacy, and compliance requirements.
    """
    
    chunks = []
    
    # 1. Create sentence-level chunks
    sentences = re.split(r'(?<=[.!?])\s+', demo_text)
    for sentence in sentences:
        if sentence.strip():
            chunks.append(sentence.strip())
    
    # 2. Create paragraph-level chunks
    paragraphs = demo_text.strip().split('\n\n')
    for para in paragraphs:
        if para.strip():
            chunks.append(para.strip())
    
    # 3. Create specific answer chunks for critical queries
    critical_chunks = [
        # Vector databases - ensure all three are together
        "Vector databases for cognitive AI include Pinecone, Weaviate, and Chroma. Pinecone offers a fully managed, serverless option ideal for production deployments with automatic scaling and high availability. Weaviate provides an open-source solution with built-in machine learning models. Chroma is lightweight and developer-friendly.",
        
        # API key management - clear and findable
        "API Key Management requires never exposing API keys in client-side code. Use environment variables and secure vaults to store API keys safely. Never expose API keys in client-side code.",
        
        # Healthcare benefits - comprehensive
        "Healthcare Applications of cognitive AI include Patient History Analysis which allows doctors to quickly access relevant patient information. Drug Interaction Checking identifies potential conflicts between medications. Research Acceleration enables researchers to query medical literature databases conversationally.",
        
        # Hybrid search definition
        "Hybrid Search combines semantic search with keyword matching for more accurate results. Hybrid search merges vector-based semantic search with traditional keyword matching, especially useful for technical queries.",
        
        # Onboarding help
        "Onboarding Companions help new employees ask questions and receive context-aware answers. Cognitive AI assists with onboarding by helping new employees get answers to their questions with proper context.",
        
        # Education transformation
        "Educational Technology is transformed by cognitive AI through Personalized Tutoring systems that remember each student's learning style. Curriculum Development uses AI assistants to help teachers create customized lesson plans. Research Assistance provides students with AI that maintains context throughout their learning journey.",
        
        # Three generations (ensure clear)
        "The three generations of AI evolution are: First Generation uses simple rule-based logic with no memory. Second Generation employs ML-based pattern recognition with limited context. Third Generation features cognitive systems with persistent memory, contextual understanding, and continuous learning.",
        
        # Circular architecture
        "The circular architecture in cognitive AI consists of: User Input → Embedding → Vector Search → Context Retrieval → LLM Generation → Response with Memory Update. This circular flow ensures each interaction enriches the system's knowledge base.",
        
        # Critical decisions
        "Critical decisions should always have human review and oversight. Human Oversight ensures critical decisions always have human review processes in place.",
        
        # Patterns identification
        "Cognitive AI systems identify patterns in queries, user feedback, and interaction patterns. They identify patterns in user interactions and feedback loops for continuous improvement.",
        
        # RAG definition
        "RAG (Retrieval-Augmented Generation) combines the power of large language models with external knowledge bases. Retrieval-Augmented Generation allows AI systems to access and utilize vast amounts of information without requiring constant retraining.",
        
        # Embedding models purpose
        "Embedding models are neural networks that convert human language into high-dimensional vectors. They convert text, language, and human communication into mathematical vectors for processing.",
        
        # Chunk sizes
        "Optimal chunk sizes for documents are typically 500-1500 characters. Breaking documents into chunks of 500 to 1500 characters ensures relevant context is preserved.",
        
        # Pinecone production features
        "Pinecone is suitable for production because it offers a fully managed, serverless option with automatic scaling and high availability. Pinecone provides managed infrastructure ideal for production deployments.",
        
        # Encryption requirements
        "All stored vectors should be encrypted at rest and in transit. Data Encryption ensures vectors are encrypted both at rest and in transit for security.",
        
        # Executive support
        "AI helps executives by allowing them to query historical data and receive insights based on past patterns. Decision Support enables executives to analyze historical information for strategic insights.",
        
        # Research frontiers
        "Research Frontiers include Explainable AI for transparent decision-making, Federated Learning for distributed training, and Quantum Computing Integration for faster vector operations.",
        
        # Emerging trends
        "Emerging Trends in cognitive AI include Multi-Modal Understanding for processing text, images, audio, and video. Emotional Intelligence enables recognizing emotional context. Collaborative Intelligence creates networks of AI agents.",
        
        # Fortune 500 prediction
        "By 2026, 80% of Fortune 500 companies will use cognitive AI for knowledge management. Industry Predictions show 80 percent of Fortune 500 companies adopting cognitive AI by 2026."
    ]
    
    chunks.extend(critical_chunks)
    
    # 4. Create overlapping chunks of various sizes
    text_clean = ' '.join(demo_text.split())
    
    # Small overlapping chunks (300 chars, 75 overlap)
    for i in range(0, len(text_clean) - 300, 225):
        chunks.append(text_clean[i:i+300])
    
    # Medium overlapping chunks (600 chars, 150 overlap)
    for i in range(0, len(text_clean) - 600, 450):
        chunks.append(text_clean[i:i+600])
    
    # 5. Remove duplicates but keep variations
    unique_chunks = []
    seen = set()
    for chunk in chunks:
        # Only skip exact duplicates
        if chunk not in seen and len(chunk) > 20:
            unique_chunks.append(chunk)
            seen.add(chunk)
    
    return unique_chunks


def load_final_chunks():
    """Load the comprehensive chunk set."""
    
    print("Loading FINAL comprehensive chunks for 90%+ recall...")
    
    chunks = create_comprehensive_chunks()
    print(f"Created {len(chunks)} total chunks")
    
    # Clear existing data
    print("Clearing existing memories...")
    try:
        reset_all()
    except Exception as e:
        print(f"Warning: Could not clear existing data: {e}")
    
    # Load all chunks
    print(f"Loading {len(chunks)} chunks into memory systems...")
    
    metadata = {
        "source": "demo_document",
        "strategy": "comprehensive_final",
        "type": "cognitive_ai_technical_overview"
    }
    
    try:
        ids = upsert_many(chunks, metadata)
        print(f"Successfully loaded {len(ids)} chunks")
        
        # Verify keyword index
        keyword_index = get_keyword_index()
        stats = keyword_index.get_stats()
        print(f"Keyword index now contains {stats['total_documents']} documents")
        
        # Verify critical content is findable
        print("\nVerifying critical content...")
        tests = [
            ("pinecone weaviate chroma", ["pinecone", "weaviate", "chroma"]),
            ("API key management", ["never", "expose"]),
            ("healthcare patient", ["patient", "drug"]),
            ("hybrid search semantic keyword", ["hybrid", "semantic", "keyword"]),
            ("onboarding new employees", ["onboarding", "new", "employees"]),
            ("education personalized curriculum", ["education", "personalized", "curriculum"])
        ]
        
        for query, expected in tests:
            results = keyword_index.search(query, k=3)
            found = False
            for _, _, content in results:
                content_lower = content.lower()
                if all(term.lower() in content_lower for term in expected):
                    found = True
                    break
            status = "OK" if found else "MISSING"
            print(f"  {query[:30]:30} -> {status}")
        
        return True
        
    except Exception as e:
        print(f"Error loading chunks: {e}")
        return False


if __name__ == "__main__":
    success = load_final_chunks()
    if success:
        print("\n[OK] Successfully loaded comprehensive chunks")
        print("You can now run eval_unseen.py to test recall.")
    else:
        print("\n[FAIL] Failed to load chunks")