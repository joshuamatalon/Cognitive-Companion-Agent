"""Script to re-ingest documents with improved chunking for better recall."""
import os
from pathlib import Path
from pypdf import PdfReader
from io import BytesIO
from vec_memory import upsert_note, reset_all, get_memory_stats
from improved_chunking import smart_chunks
import time
import json

def reingest_pdf(file_path: str, chunk_size: int = 1200, overlap: int = 200):
    """Re-ingest a PDF file with smart chunking."""
    print(f"\nProcessing: {file_path}")
    
    # Read the PDF
    with open(file_path, 'rb') as f:
        pdf_bytes = f.read()
    
    reader = PdfReader(BytesIO(pdf_bytes))
    total_chunks = 0
    
    # Extract text from all pages
    all_text = []
    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if text:
            all_text.append(f"\n--- Page {page_num} ---\n{text}")
    
    # Combine all text
    full_text = "\n".join(all_text)
    
    # Use smart chunking with overlap
    chunks = smart_chunks(full_text, chunk_size=chunk_size, overlap=overlap)
    
    print(f"Created {len(chunks)} chunks with {overlap} char overlap")
    
    # Ingest each chunk
    for i, chunk in enumerate(chunks):
        metadata = {
            "source": Path(file_path).name,
            "type": "pdf",
            "chunk_index": i,
            "total_chunks": len(chunks),
            "chunking_method": "smart_overlap",
            "chunk_size": chunk_size,
            "overlap": overlap
        }
        
        # Extract key information for better searchability
        if "$" in chunk:
            metadata["contains_dollar"] = True
        if any(word in chunk.lower() for word in ["education", "healthcare", "enterprise"]):
            metadata["domain"] = True
        if any(word in chunk.lower() for word in ["security", "privacy", "access control"]):
            metadata["security_related"] = True
            
        try:
            upsert_note(chunk, metadata)
            total_chunks += 1
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(chunks)} chunks...")
        except Exception as e:
            print(f"  Error ingesting chunk {i}: {e}")
    
    print(f"Successfully ingested {total_chunks} chunks from {file_path}")
    return total_chunks


def reingest_demo_content():
    """Re-ingest demo content with improved chunking."""
    print("Re-ingesting Demo Document content with improved chunking...")
    
    # Define demo content based on what we know is in the Demo Document
    demo_content = """
    Cognitive AI systems are characterized by persistent memory, contextual understanding, and adaptive learning.
    These systems combine multiple capabilities to create intelligent assistants that can learn and improve over time.
    
    Ethical AI involves bias mitigation, transparency, and human oversight. It's essential to ensure AI systems
    are fair, explainable, and aligned with human values. This includes implementing proper safeguards and
    monitoring systems to prevent unintended consequences.
    
    Role-based access control ensures users access only appropriate information. This is a critical security
    feature for enterprise AI systems, preventing unauthorized access to sensitive data and maintaining
    compliance with data protection regulations.
    
    Cognitive AI is transforming enterprise knowledge management, healthcare, and education. In education,
    AI assistants help with personalized learning styles, student progress tracking, and curriculum development.
    These systems adapt to individual student needs and provide targeted support.
    
    Explainable AI makes AI decision-making processes transparent and understandable. This transparency is
    crucial for building trust in AI systems and ensuring accountability in critical applications.
    
    Security and privacy in cognitive AI systems include API key management, data encryption, and access control.
    These measures are critical for enterprise AI adoption, ensuring compliance with regulations and protecting
    sensitive information.
    
    Emotional intelligence in AI enhances user interaction by recognizing emotional contexts and responding
    appropriately. Natural language processing enables more intuitive communication between humans and AI systems.
    
    Continuous learning enables adaptive improvement and pattern recognition in AI systems. This allows systems
    to become more effective over time, learning from user interactions and feedback.
    
    Cognitive AI assistants are becoming standard in professional workflows, improving productivity and
    decision-making across various industries. The integration of AI into daily work processes is accelerating
    as these systems become more capable and reliable.
    """
    
    # Use smart chunking
    chunks = smart_chunks(demo_content, chunk_size=800, overlap=200)
    
    print(f"Created {len(chunks)} chunks from demo content")
    
    total_ingested = 0
    for i, chunk in enumerate(chunks):
        metadata = {
            "source": "demo_content_reingest",
            "type": "text",
            "chunk_index": i,
            "total_chunks": len(chunks),
            "reingest_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            upsert_note(chunk, metadata)
            total_ingested += 1
        except Exception as e:
            print(f"Error ingesting chunk {i}: {e}")
    
    print(f"Successfully ingested {total_ingested} demo content chunks")
    return total_ingested


def main():
    """Main re-ingestion process."""
    print("="*60)
    print("DOCUMENT RE-INGESTION TOOL")
    print("="*60)
    
    # Check current status
    stats = get_memory_stats()
    print(f"\nCurrent database status:")
    print(f"  Total memories: {stats['total_memories']}")
    print(f"  Index: {stats['index_name']}")
    
    # Ask user what to do
    print("\nOptions:")
    print("1. Re-ingest Demo Document content (recommended)")
    print("2. Re-ingest a specific PDF file")
    print("3. Clear database and start fresh")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        total = reingest_demo_content()
        print(f"\n[OK] Re-ingestion complete! Added {total} chunks.")
        
    elif choice == "2":
        file_path = input("Enter PDF file path: ").strip()
        if os.path.exists(file_path):
            total = reingest_pdf(file_path)
            print(f"\n[OK] Re-ingestion complete! Added {total} chunks.")
        else:
            print(f"Error: File not found: {file_path}")
            
    elif choice == "3":
        confirm = input("Are you sure you want to clear the database? (yes/no): ").strip().lower()
        if confirm == "yes":
            reset_all()
            print("[OK] Database cleared.")
            
    elif choice == "4":
        print("Exiting...")
    else:
        print("Invalid choice.")
    
    # Show new stats
    if choice in ["1", "2", "3"]:
        stats = get_memory_stats()
        print(f"\nNew database status:")
        print(f"  Total memories: {stats['total_memories']}")


if __name__ == "__main__":
    main()