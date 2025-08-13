"""Improved chunking with overlap to prevent information loss at boundaries."""
import re
from typing import List, Optional

def smart_chunks(text: str, chunk_size: int = 1200, overlap: int = 200) -> List[str]:
    """
    Create overlapping chunks, breaking at sentence boundaries when possible.
    
    Args:
        text: The text to chunk
        chunk_size: Target size for each chunk (default 1200 chars)
        overlap: Number of characters to overlap between chunks (default 200 chars)
    
    Returns:
        List of text chunks with overlap
    """
    if not text or not text.strip():
        return []
    
    # Clean the text
    text = text.replace("\x00", "")
    text = text.strip()
    
    # If text is shorter than chunk_size, return as single chunk
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    
    # Find sentence boundaries (. ! ? followed by space or newline)
    sentence_endings = re.compile(r'[.!?][\s\n]')
    
    current_pos = 0
    
    while current_pos < len(text):
        # Determine the end position for this chunk
        chunk_end = min(current_pos + chunk_size, len(text))
        
        # If we're not at the end of the text, try to break at a sentence boundary
        if chunk_end < len(text):
            # Look for the last sentence ending before chunk_end
            search_text = text[current_pos:chunk_end]
            matches = list(sentence_endings.finditer(search_text))
            
            if matches:
                # Use the last sentence boundary found
                last_match = matches[-1]
                chunk_end = current_pos + last_match.end()
            else:
                # No sentence boundary found, try to break at a word boundary
                # Look for the last space before chunk_end
                space_pos = text.rfind(' ', current_pos, chunk_end)
                if space_pos > current_pos:
                    chunk_end = space_pos
        
        # Extract the chunk
        chunk = text[current_pos:chunk_end].strip()
        
        if chunk:
            chunks.append(chunk)
        
        # Move to the next position with overlap
        if chunk_end >= len(text):
            break
        
        # Calculate the next starting position with overlap
        next_pos = chunk_end - overlap
        
        # Ensure we make progress
        if next_pos <= current_pos:
            next_pos = chunk_end
        
        current_pos = next_pos
    
    return chunks


def chunk_with_metadata(
    text: str, 
    chunk_size: int = 1200, 
    overlap: int = 200,
    source: Optional[str] = None,
    page: Optional[int] = None
) -> List[dict]:
    """
    Create chunks with metadata for better tracking.
    
    Args:
        text: The text to chunk
        chunk_size: Target size for each chunk
        overlap: Overlap between chunks
        source: Source document name
        page: Page number if applicable
    
    Returns:
        List of dictionaries with chunk text and metadata
    """
    chunks = smart_chunks(text, chunk_size, overlap)
    
    result = []
    for i, chunk in enumerate(chunks):
        metadata = {
            'chunk_index': i,
            'chunk_size': len(chunk),
            'total_chunks': len(chunks)
        }
        
        if source:
            metadata['source'] = source
        if page is not None:
            metadata['page'] = page
        
        # Extract key information from chunk for better searchability
        numbers = re.findall(r'\$?[\d,]+(?:\.\d{2})?', chunk)
        if numbers:
            metadata['contains_numbers'] = True
            metadata['numbers'] = numbers[:5]  # Store first 5 numbers
        
        # Check for percentage values
        percentages = re.findall(r'\d+(?:\.\d+)?%', chunk)
        if percentages:
            metadata['contains_percentages'] = True
            metadata['percentages'] = percentages[:3]
        
        # Check for time periods
        time_periods = re.findall(r'\d+[-–]\d+\s*(?:month|year|week|day)s?', chunk)
        if time_periods:
            metadata['contains_time_periods'] = True
            metadata['time_periods'] = time_periods[:3]
        
        result.append({
            'text': chunk,
            'metadata': metadata
        })
    
    return result


def test_chunking():
    """Test the chunking function with sample text."""
    sample_text = """
    Josh's 18-24 month objective is to build equity in frontier AI companies. 
    He plans to use tools like LangChain, Pinecone, and GitHub in Phase 1.
    His monthly student loan payment is $2,100, with a total debt of $128,000.
    
    This is a longer paragraph that will demonstrate how the chunking works with overlapping segments.
    The overlap ensures that important information isn't lost at chunk boundaries. When we split text
    into chunks, we want to make sure that sentences aren't cut in the middle. This approach helps
    maintain context and improves search recall significantly.
    
    Another important aspect is handling different types of content. Numbers like 42, percentages like 85%,
    and dollar amounts like $50,000 should all be preserved correctly. Time periods such as 6-12 months
    should also be kept intact.
    """
    
    # Test basic chunking
    chunks = smart_chunks(sample_text, chunk_size=200, overlap=50)
    
    print("Basic Chunking Test:")
    print(f"Original text length: {len(sample_text)}")
    print(f"Number of chunks: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1} (length: {len(chunk)}):")
        print(chunk[:100] + "..." if len(chunk) > 100 else chunk)
    
    # Test chunking with metadata
    print("\n" + "="*60)
    print("Chunking with Metadata Test:")
    
    chunks_with_meta = chunk_with_metadata(
        sample_text, 
        chunk_size=200, 
        overlap=50,
        source="test_document.txt",
        page=1
    )
    
    for i, item in enumerate(chunks_with_meta):
        print(f"\nChunk {i+1}:")
        print(f"  Text preview: {item['text'][:50]}...")
        print(f"  Metadata: {item['metadata']}")


if __name__ == "__main__":
    test_chunking()