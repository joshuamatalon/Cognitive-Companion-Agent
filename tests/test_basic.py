"""Basic test suite for Cognitive Companion App."""
import pytest
import time
import uuid
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vec_memory import upsert_note, search, delete_by_ids, get_memory_stats
from search_enhancements import enhanced_search, extract_key_terms, extract_patterns
from improved_chunking import smart_chunks


class TestVectorMemory:
    """Test vector memory operations."""
    
    def test_upsert_note_returns_valid_id(self):
        """Test that upsert_note returns a valid ID."""
        test_text = "This is a test note for the Cognitive Companion."
        metadata = {"type": "test", "timestamp": "2025-01-13"}
        
        note_id = upsert_note(test_text, metadata)
        
        assert note_id is not None
        assert len(note_id) > 0
        assert isinstance(note_id, str)
        
        # Clean up
        delete_by_ids([note_id])
    
    def test_search_finds_recently_added_content(self):
        """Test that search finds recently added content."""
        unique_text = f"Unique test content {uuid.uuid4()}"
        metadata = {"type": "test"}
        
        # Add content
        note_id = upsert_note(unique_text, metadata)
        
        # Wait a moment for indexing
        time.sleep(2)
        
        # Search for it
        results = search("Unique test content", k=5)
        
        assert len(results) > 0
        found = any(unique_text in (r[1] or "") for r in results)
        assert found, f"Could not find '{unique_text}' in search results"
        
        # Clean up
        delete_by_ids([note_id])
    
    def test_empty_query_doesnt_crash(self):
        """Test that empty/nonsense queries don't crash."""
        # Empty query should be handled gracefully (may raise an error, which is fine)
        try:
            results = search("", k=5)
            assert results is not None
        except (RuntimeError, ValueError) as e:
            # It's acceptable for empty queries to raise an error
            assert "empty" in str(e).lower() or "invalid" in str(e).lower()
        
        # Nonsense query should work without crashing
        try:
            results = search("asdfghjklqwertyuiop", k=5)
            assert results is not None
        except Exception as e:
            pytest.fail(f"Nonsense query crashed: {e}")
    
    def test_metadata_preservation(self):
        """Test that metadata is preserved correctly."""
        test_text = f"Metadata test {uuid.uuid4()}"
        metadata = {
            "type": "test",
            "source": "test_file.txt",
            "page": 5,
            "custom_field": "custom_value"
        }
        
        note_id = upsert_note(test_text, metadata)
        time.sleep(2)
        
        results = search(test_text, k=1)
        
        assert len(results) > 0
        _, _, result_meta = results[0]
        
        # Check that key metadata fields are preserved
        assert result_meta.get("type") == "test"
        assert result_meta.get("source") == "test_file.txt"
        
        # Clean up
        delete_by_ids([note_id])
    
    def test_deletion_works(self):
        """Test that deletion actually removes content."""
        unique_text = f"Delete test {uuid.uuid4()}"
        metadata = {"type": "test"}
        
        # Add content
        note_id = upsert_note(unique_text, metadata)
        time.sleep(2)
        
        # Verify it's there
        results = search(unique_text, k=5)
        assert len(results) > 0
        
        # Delete it
        delete_by_ids([note_id])
        time.sleep(2)
        
        # Verify it's gone
        results = search(unique_text, k=5)
        found = any(unique_text in (r[1] or "") for r in results)
        assert not found, "Content still found after deletion"
    
    def test_search_latency(self):
        """Test that search latency is under 5 seconds."""
        start_time = time.time()
        results = search("test query for latency", k=5)
        end_time = time.time()
        
        latency = end_time - start_time
        assert latency < 5.0, f"Search took {latency:.2f} seconds, exceeding 5 second limit"
    
    def test_memory_stats_available(self):
        """Test that memory stats are available."""
        stats = get_memory_stats()
        
        assert stats is not None
        assert "total_memories" in stats
        assert "index_name" in stats
        assert stats["index_name"] == "cca-memories"
        assert isinstance(stats["total_memories"], int)


class TestSearchEnhancements:
    """Test enhanced search functionality."""
    
    def test_extract_key_terms(self):
        """Test key term extraction."""
        query = "What is my monthly student loan payment?"
        key_terms = extract_key_terms(query)
        
        assert "monthly" in key_terms
        assert "student" in key_terms
        assert "loan" in key_terms
        assert "payment" in key_terms
        assert "what" not in key_terms.lower()  # Stop word should be removed
    
    def test_extract_patterns(self):
        """Test pattern extraction."""
        query = "My payment is $2,100 per month for 18-24 months at 5.5%"
        patterns = extract_patterns(query)
        
        assert "$2,100" in patterns or "2,100" in patterns
        assert "18-24 month" in patterns or "18" in patterns
        assert "5.5%" in patterns or "5.5" in patterns
    
    def test_enhanced_search_returns_results(self):
        """Test that enhanced search returns results."""
        results = enhanced_search("test query", k=5)
        
        assert results is not None
        assert isinstance(results, list)
        assert len(results) <= 5  # Should respect k parameter


class TestChunking:
    """Test improved chunking functionality."""
    
    def test_smart_chunks_basic(self):
        """Test basic smart chunking."""
        text = "This is sentence one. This is sentence two. This is sentence three."
        chunks = smart_chunks(text, chunk_size=30, overlap=10)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk) > 0 for chunk in chunks)
    
    def test_chunks_have_overlap(self):
        """Test that chunks have proper overlap."""
        text = "A" * 100 + " " + "B" * 100 + " " + "C" * 100
        chunks = smart_chunks(text, chunk_size=150, overlap=50)
        
        assert len(chunks) >= 2
        # Check that there's some content repeated between chunks
        if len(chunks) >= 2:
            # There should be some overlap between consecutive chunks
            overlap_found = any(
                chunk1[-20:] in chunk2 
                for chunk1, chunk2 in zip(chunks[:-1], chunks[1:])
            )
            assert overlap_found or len(chunks) == 1


def test_known_good_query():
    """Test a known good query (Josh's objectives)."""
    # This test may fail if the database doesn't have the right content
    # It's here to verify when proper content is loaded
    
    # Add test content
    test_content = "Josh's 18-24 month objective is to build equity in frontier AI companies."
    note_id = upsert_note(test_content, {"type": "test", "source": "test"})
    
    time.sleep(2)
    
    # Search for it
    results = search("Josh objective equity", k=5)
    
    # Check if we found relevant content
    found = False
    for _, text, _ in results:
        if text and ("josh" in text.lower() or "equity" in text.lower()):
            found = True
            break
    
    # Clean up
    delete_by_ids([note_id])
    
    assert found, "Could not find Josh's objectives in search results"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])