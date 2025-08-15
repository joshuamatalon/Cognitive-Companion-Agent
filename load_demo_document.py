"""
Load the demo document into both vector and keyword indices.
"""

import re
from vec_memory import upsert_many, reset_all
from keyword_search import get_keyword_index


def extract_text_from_demo():
    """Extract and chunk the demo document text."""
    
    # The demo document content
    demo_text = """
    Introduction to Cognitive AI Systems
    A Technical Overview for Modern Applications
    
    Executive Summary
    Cognitive AI systems represent the next evolution in artificial intelligence, moving beyond simple pattern recognition to systems that can understand, learn, and maintain context over time. This document explores the fundamental concepts, architectures, and applications of cognitive AI systems in enterprise environments.
    
    Chapter 1: Understanding Cognitive AI
    
    What Makes AI "Cognitive"?
    Cognitive AI systems distinguish themselves from traditional AI through several key characteristics:
    
    Persistent Memory: Unlike traditional chatbots that forget conversations after each session, cognitive AI systems maintain long-term memory of interactions, facts, and learned patterns. This enables them to build upon previous knowledge and provide increasingly personalized responses.
    
    Contextual Understanding: These systems don't just process words; they understand context, relationships, and implications. They can connect disparate pieces of information to form coherent understanding.
    
    Adaptive Learning: Cognitive AI systems improve over time through interaction. They learn from user feedback, identify patterns in queries, and adjust their responses based on accumulated knowledge.
    
    The Evolution from Chatbots to Cognitive Companions
    The journey from simple rule-based chatbots to cognitive AI companions represents a fundamental shift in how we interact with artificial intelligence:
    
    First Generation (Rule-Based): Simple if-then logic, no memory
    Second Generation (ML-Based): Pattern recognition, limited context
    Third Generation (Cognitive): Persistent memory, contextual understanding, continuous learning
    
    Chapter 2: Technical Architecture
    
    Core Components of Cognitive Systems
    
    Vector Databases: The backbone of modern cognitive AI is the vector database. Unlike traditional databases that store exact values, vector databases store mathematical representations of concepts, enabling semantic search and similarity matching.
    
    Embedding Models: These neural networks convert human language into high-dimensional vectors. Popular models include OpenAI's text-embedding-3, Google's PaLM embeddings, and open-source alternatives like Sentence-BERT.
    
    Retrieval-Augmented Generation (RAG): RAG combines the power of large language models with external knowledge bases. This architecture allows AI systems to access and utilize vast amounts of information without requiring constant retraining.
    
    System Architecture Overview
    User Input → Embedding → Vector Search → Context Retrieval → LLM Generation → Response
    Memory Update
    
    This circular architecture ensures that each interaction enriches the system's knowledge base, creating a continuously improving experience.
    
    Chapter 3: Implementation Strategies
    
    Choosing the Right Vector Database
    When implementing a cognitive AI system, selecting the appropriate vector database is crucial:
    
    Pinecone: Fully managed, serverless option ideal for production deployments. Offers automatic scaling and high availability.
    
    Weaviate: Open-source solution with built-in machine learning models. Excellent for organizations wanting full control.
    
    Chroma: Lightweight, developer-friendly option perfect for prototypes and smaller applications.
    
    Optimization Techniques
    
    Chunking Strategies: Breaking documents into optimal chunk sizes (typically 500-1500 characters) ensures relevant context without overwhelming the language model.
    
    Hybrid Search: Combining semantic search with keyword matching provides more accurate results, especially for technical queries.
    
    Caching Layers: Implementing intelligent caching reduces API calls and improves response times for frequently asked questions.
    
    Chapter 4: Real-World Applications
    
    Enterprise Knowledge Management
    Cognitive AI systems are revolutionizing how organizations manage and access institutional knowledge:
    
    • Documentation Assistant: Instantly search through thousands of pages of technical documentation
    • Onboarding Companion: New employees can ask questions and receive context-aware answers
    • Decision Support: Executives can query historical data and receive insights based on past patterns
    
    Healthcare Applications
    The healthcare industry is seeing significant benefits from cognitive AI:
    
    • Patient History Analysis: Doctors can quickly access relevant patient information from years of records
    • Drug Interaction Checking: AI systems can identify potential conflicts across complex medication regimens
    • Research Acceleration: Researchers can query vast medical literature databases conversationally
    
    Educational Technology
    Cognitive AI is transforming education through:
    
    • Personalized Tutoring: Systems that remember each student's learning style and progress
    • Curriculum Development: AI assistants that help teachers create customized lesson plans
    • Research Assistance: Students can explore complex topics with AI that maintains context throughout their learning journey
    
    Chapter 5: Best Practices and Considerations
    
    Security and Privacy
    When implementing cognitive AI systems, security must be paramount:
    
    API Key Management: Never expose API keys in client-side code. Use environment variables and secure vaults.
    
    Data Encryption: All stored vectors should be encrypted at rest and in transit.
    
    Access Control: Implement role-based access control to ensure users only access appropriate information.
    
    Performance Optimization
    
    Batch Processing: Process multiple queries simultaneously to reduce latency.
    
    Asynchronous Operations: Use async/await patterns to prevent blocking operations.
    
    Resource Management: Monitor token usage and implement rate limiting to control costs.
    
    Ethical Considerations
    
    Bias Mitigation: Regularly audit AI responses for potential biases and implement correction mechanisms.
    
    Transparency: Users should understand when they're interacting with AI and how their data is being used.
    
    Human Oversight: Critical decisions should always have human review processes in place.
    
    Chapter 6: Future Directions
    
    Emerging Trends
    The field of cognitive AI is rapidly evolving with several exciting developments:
    
    Multi-Modal Understanding: Future systems will seamlessly process text, images, audio, and video.
    
    Emotional Intelligence: AI systems are beginning to recognize and respond to emotional context.
    
    Collaborative Intelligence: Networks of AI agents working together to solve complex problems.
    
    Research Frontiers
    Current research is pushing boundaries in several areas:
    
    • Explainable AI: Making AI decision-making processes transparent and understandable
    • Federated Learning: Training AI systems across distributed data without centralizing information
    • Quantum Computing Integration: Leveraging quantum computers for exponentially faster vector operations
    
    Industry Predictions
    By 2026, we expect to see:
    
    • 80% of Fortune 500 companies using cognitive AI for knowledge management
    • Cognitive AI assistants becoming standard in professional workflows
    • New job categories emerging around AI system training and maintenance
    
    Conclusion
    Cognitive AI systems represent a fundamental shift in how we interact with information and technology. By combining persistent memory, contextual understanding, and continuous learning, these systems are becoming true partners in human endeavor rather than mere tools.
    
    The key to successful implementation lies in understanding both the technical architecture and the human needs these systems serve. As we move forward, the organizations that best leverage cognitive AI will have significant competitive advantages in their respective fields.
    """
    
    # Split into chunks
    chunks = []
    
    # Split by paragraphs and chapters
    paragraphs = [p.strip() for p in demo_text.split('\n\n') if p.strip()]
    
    for para in paragraphs:
        # Skip very short paragraphs
        if len(para) < 50:
            continue
            
        # If paragraph is too long, split it further
        if len(para) > 1500:
            sentences = para.split('. ')
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) < 1200:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + ". "
            if current_chunk:
                chunks.append(current_chunk.strip())
        else:
            chunks.append(para)
    
    return chunks


def load_demo_document():
    """Load demo document into both vector and keyword indices."""
    
    print("Loading demo document into memory systems...")
    
    # Extract chunks from demo document
    chunks = extract_text_from_demo()
    print(f"Extracted {len(chunks)} chunks from demo document")
    
    # Clear existing data first
    print("Clearing existing memories...")
    try:
        reset_all()
    except Exception as e:
        print(f"Warning: Could not clear existing data: {e}")
    
    # Also clear keyword index
    try:
        keyword_index = get_keyword_index()
        keyword_index.clear_all()
        print("Keyword index cleared")
    except Exception as e:
        print(f"Warning: Could not clear keyword index: {e}")
    
    # Load chunks into vector database (this will also add to keyword index)
    print(f"Loading {len(chunks)} chunks into memory systems...")
    
    metadata = {
        "source": "demo_document",
        "type": "cognitive_ai_technical_overview"
    }
    
    try:
        ids = upsert_many(chunks, metadata)
        print(f"Successfully loaded {len(ids)} chunks")
        
        # Verify keyword index
        keyword_index = get_keyword_index()
        stats = keyword_index.get_stats()
        print(f"Keyword index now contains {stats['total_documents']} documents")
        
    except Exception as e:
        print(f"Error loading chunks: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = load_demo_document()
    if success:
        print("\nDemo document successfully loaded!")
        print("You can now run eval.py to test the hybrid search performance.")
    else:
        print("\nFailed to load demo document.")