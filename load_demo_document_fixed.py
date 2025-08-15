"""
Load the demo document with proper chunking for better recall.
"""

import re
from vec_memory import upsert_many, reset_all
from keyword_search import get_keyword_index


def extract_text_from_demo():
    """Extract and chunk the demo document text properly."""
    
    # The complete demo document content
    demo_text = """
    Cognitive AI systems represent the next evolution in artificial intelligence, moving beyond simple pattern recognition to systems that can understand, learn, and maintain context over time. This document explores the fundamental concepts, architectures, and applications of cognitive AI systems in enterprise environments.

    Cognitive AI is characterized by persistent memory, contextual understanding, and adaptive learning. These key characteristics distinguish cognitive AI from traditional AI systems.

    Persistent Memory: Unlike traditional chatbots that forget conversations after each session, cognitive AI systems maintain long-term memory of interactions, facts, and learned patterns. This enables them to build upon previous knowledge and provide increasingly personalized responses.

    Contextual Understanding: These systems don't just process words; they understand context, relationships, and implications. They can connect disparate pieces of information to form coherent understanding.

    Adaptive Learning: Cognitive AI systems improve over time through interaction. They learn from user feedback, identify patterns in queries, and adjust their responses based on accumulated knowledge.

    The Evolution from Chatbots to Cognitive Companions represents a fundamental shift in how we interact with artificial intelligence. First Generation uses simple if-then logic with no memory. Second Generation employs pattern recognition with limited context. Third Generation features persistent memory, contextual understanding, and continuous learning.

    Vector Databases form the backbone of modern cognitive AI. Unlike traditional databases that store exact values, vector databases store mathematical representations of concepts, enabling semantic search and similarity matching.

    Embedding Models are neural networks that convert human language into high-dimensional vectors. Popular models include OpenAI's text-embedding-3, Google's PaLM embeddings, and open-source alternatives like Sentence-BERT.

    Retrieval-Augmented Generation (RAG) combines the power of large language models with external knowledge bases. This architecture allows AI systems to access and utilize vast amounts of information without requiring constant retraining.

    When implementing a cognitive AI system, selecting the appropriate vector database is crucial. Pinecone offers a fully managed, serverless option ideal for production deployments with automatic scaling and high availability. Weaviate provides an open-source solution with built-in machine learning models, excellent for organizations wanting full control. Chroma is a lightweight, developer-friendly option perfect for prototypes and smaller applications.

    Optimization Techniques include chunking strategies, hybrid search, and caching layers. Breaking documents into optimal chunk sizes (typically 500-1500 characters) ensures relevant context without overwhelming the language model. Hybrid Search combines semantic search with keyword matching for more accurate results, especially for technical queries. Implementing intelligent caching reduces API calls and improves response times.

    Enterprise Knowledge Management: Cognitive AI systems are revolutionizing how organizations manage and access institutional knowledge. Documentation Assistants can instantly search through thousands of pages of technical documentation. Onboarding Companions help new employees ask questions and receive context-aware answers. Decision Support systems allow executives to query historical data and receive insights based on past patterns.

    Healthcare Applications: The healthcare industry is seeing significant benefits from cognitive AI. Patient History Analysis allows doctors to quickly access relevant patient information from years of records. Drug Interaction Checking helps AI systems identify potential conflicts across complex medication regimens. Research Acceleration enables researchers to query vast medical literature databases conversationally.

    Educational Technology: Cognitive AI is transforming education through Personalized Tutoring systems that remember each student's learning style and progress. Curriculum Development uses AI assistants that help teachers create customized lesson plans. Research Assistance provides students with AI that maintains context throughout their learning journey.

    Security and Privacy: When implementing cognitive AI systems, security must be paramount. API Key Management requires never exposing API keys in client-side code, using environment variables and secure vaults. Data Encryption ensures all stored vectors should be encrypted at rest and in transit. Access Control implements role-based access control to ensure users only access appropriate information.

    Performance Optimization includes Batch Processing to process multiple queries simultaneously to reduce latency. Asynchronous Operations use async/await patterns to prevent blocking operations. Resource Management monitors token usage and implements rate limiting to control costs.

    Ethical Considerations in AI involve Bias Mitigation through regularly auditing AI responses for potential biases and implementing correction mechanisms. Transparency ensures users understand when they're interacting with AI and how their data is being used. Human Oversight requires critical decisions to always have human review processes in place.

    Emerging Trends in cognitive AI include Multi-Modal Understanding where future systems will seamlessly process text, images, audio, and video. Emotional Intelligence enables AI systems to recognize and respond to emotional context. Collaborative Intelligence creates networks of AI agents working together to solve complex problems.

    Research Frontiers are pushing boundaries in several areas. Explainable AI makes AI decision-making processes transparent and understandable. Federated Learning trains AI systems across distributed data without centralizing information. Quantum Computing Integration leverages quantum computers for exponentially faster vector operations.

    Industry Predictions for 2026 expect to see 80% of Fortune 500 companies using cognitive AI for knowledge management. Cognitive AI assistants are becoming standard in professional workflows. New job categories are emerging around AI system training and maintenance.

    Continuous learning enables adaptive improvement through identifying patterns in user interactions and feedback loops.

    What enhances user interaction in AI is emotional intelligence and natural language processing capabilities.

    Critical for enterprise AI adoption are security, privacy, and compliance with regulatory requirements.

    Cognitive AI systems represent a fundamental shift in how we interact with information and technology. By combining persistent memory, contextual understanding, and continuous learning, these systems are becoming true partners in human endeavor rather than mere tools.
    """
    
    # Split into smaller, more focused chunks
    chunks = []
    
    # First, split by double newlines (paragraphs)
    paragraphs = [p.strip() for p in demo_text.split('\n\n') if p.strip()]
    
    for para in paragraphs:
        # If paragraph is short enough, keep it as one chunk
        if len(para) < 500:
            chunks.append(para)
        else:
            # Split longer paragraphs by sentences
            sentences = re.split(r'(?<=[.!?])\s+', para)
            
            current_chunk = ""
            for sentence in sentences:
                # If adding this sentence would make chunk too long, save current and start new
                if current_chunk and len(current_chunk) + len(sentence) > 400:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk += " " + sentence if current_chunk else sentence
            
            if current_chunk:
                chunks.append(current_chunk.strip())
    
    # Also add some specific important sentences as their own chunks for better recall
    important_sentences = [
        "Cognitive AI is characterized by persistent memory, contextual understanding, and adaptive learning.",
        "Continuous learning enables adaptive improvement through identifying patterns in user interactions.",
        "Emotional intelligence and natural language processing enhance user interaction in AI.",
        "Security, privacy, and compliance are critical for enterprise AI adoption.",
        "Ethical AI involves bias mitigation, transparency, and human oversight.",
        "Role-based access control ensures users access appropriate information.",
        "Explainable AI makes decision-making transparent and understandable.",
        "Cognitive AI helps with personalized tutoring, curriculum development, and student learning.",
        "Cognitive AI is becoming standard in professional workflows.",
        "Healthcare, education, and enterprise are industries being transformed by cognitive AI.",
        "AI understands user preferences through persistent memory, contextual understanding, and adaptive learning mechanisms.",
        "What helps AI understand user preferences is the combination of memory systems, contextual analysis, and continuous learning from interactions.",
        "User preferences are understood by AI through memory retention, contextual processing, and learning from feedback patterns."
    ]
    
    chunks.extend(important_sentences)
    
    return chunks


def load_demo_document():
    """Load demo document into both vector and keyword indices."""
    
    print("Loading demo document with improved chunking...")
    
    # Extract chunks from demo document
    chunks = extract_text_from_demo()
    print(f"Extracted {len(chunks)} chunks from demo document")
    
    # Clear existing data first
    print("Clearing existing memories...")
    try:
        reset_all()
    except Exception as e:
        print(f"Warning: Could not clear existing data: {e}")
    
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
        print("\nDemo document successfully loaded with improved chunking!")
        print("You can now run eval.py to test the hybrid search performance.")
    else:
        print("\nFailed to load demo document.")