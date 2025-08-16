"""
pytest configuration and shared fixtures for testing.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import io
import time
from typing import List, Dict, Any

# Configure pytest
pytest_plugins = []

@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing."""
    with patch('vec_memory.oa') as mock_oa:
        # Mock embedding response
        mock_oa.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )
        yield mock_oa

@pytest.fixture
def mock_openai_with_responses():
    """Mock OpenAI with configurable responses."""
    with patch('vec_memory.oa') as mock_oa:
        # Allow customizable embeddings
        def create_embeddings(model, input):
            embeddings = []
            for _ in input:
                # Create unique embeddings for each input
                embeddings.append(Mock(embedding=[0.1 + len(embeddings) * 0.01] * 1536))
            return Mock(data=embeddings)
        
        mock_oa.embeddings.create.side_effect = create_embeddings
        yield mock_oa

@pytest.fixture
def mock_pinecone():
    """Mock Pinecone client for testing."""
    with patch('vec_memory.pc') as mock_pc:
        with patch('vec_memory.index') as mock_index:
            # Mock query response
            mock_index.query.return_value = Mock(
                matches=[
                    Mock(
                        id="test-1", 
                        score=0.95, 
                        metadata={"text": "Cognitive AI enables persistent memory"}
                    ),
                    Mock(
                        id="test-2", 
                        score=0.90, 
                        metadata={"text": "Vector databases store embeddings"}
                    )
                ]
            )
            
            # Mock describe_index_stats
            mock_index.describe_index_stats.return_value = Mock(
                total_vector_count=1000
            )
            
            # Mock upsert
            mock_index.upsert.return_value = None
            
            # Mock delete
            mock_index.delete.return_value = None
            
            yield mock_index

@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    with patch('hybrid_rag.ChatOpenAI') as mock_chat:
        mock_instance = Mock()
        mock_chat.return_value = mock_instance
        
        # Default response
        mock_instance.invoke.return_value = Mock(
            content="Based on the context, cognitive AI uses vector databases."
        )
        
        yield mock_instance

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create necessary subdirectories
    (data_dir / "search_cache").mkdir()
    
    # Patch the data directory path
    with patch('pathlib.Path.cwd') as mock_cwd:
        mock_cwd.return_value = tmp_path
        yield data_dir

@pytest.fixture
def sample_pdf():
    """Create a sample PDF for testing."""
    from pypdf import PdfWriter, PdfReader
    import io
    
    writer = PdfWriter()
    
    # Create a page with text
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Add text content
    c.drawString(100, 750, "Cognitive Companion Agent Test Document")
    c.drawString(100, 700, "This document tests PDF ingestion capabilities.")
    c.drawString(100, 650, "It contains information about AI and vector databases.")
    c.drawString(100, 600, "Vector databases enable semantic search.")
    c.drawString(100, 550, "Hybrid search combines multiple strategies.")
    
    c.save()
    buffer.seek(0)
    
    # Read the PDF back
    reader = PdfReader(buffer)
    for page in reader.pages:
        writer.add_page(page)
    
    # Write to new buffer
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer

@pytest.fixture
def sample_pdf_simple():
    """Create a simple PDF without reportlab dependency."""
    content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >>
   /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 200 >>
stream
BT
/F1 12 Tf
100 700 Td
(Cognitive AI Test Document) Tj
0 -20 Td
(This tests PDF processing.) Tj
0 -20 Td
(Vector databases enable search.) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000292 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
542
%%EOF"""
    
    return io.BytesIO(content)

@pytest.fixture
def eval_dataset():
    """Load evaluation dataset for testing."""
    return [
        {
            "q": "What is hybrid search?",
            "expect": ["semantic", "keyword", "combines"]
        },
        {
            "q": "How should API keys be managed?",
            "expect": ["environment", "never expose", "secure"]
        },
        {
            "q": "Which vector databases are mentioned?",
            "expect": ["Pinecone", "Weaviate", "Chroma"]
        },
        {
            "q": "What benefits does cognitive AI provide?",
            "expect": ["persistent memory", "contextual", "adaptive"]
        },
        {
            "q": "How does RAG architecture work?",
            "expect": ["retrieval", "augmented", "generation"]
        }
    ]

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    with patch('config.config') as mock_cfg:
        mock_cfg.OPENAI_API_KEY = "test-key"
        mock_cfg.PINECONE_API_KEY = "test-pinecone-key"
        mock_cfg.PINECONE_ENV = "test-env"
        mock_cfg.is_valid.return_value = True
        mock_cfg.errors = []
        yield mock_cfg

@pytest.fixture
def mock_secure_config():
    """Mock secure configuration."""
    with patch('secure_config.SecureConfig') as mock_secure:
        instance = Mock()
        mock_secure.return_value = instance
        
        instance.OPENAI_API_KEY = "encrypted-openai-key"
        instance.PINECONE_API_KEY = "encrypted-pinecone-key"
        instance.validate.return_value = True
        
        yield instance

@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter that always allows requests."""
    with patch('rate_limiter.RateLimiter') as mock_rl:
        instance = Mock()
        mock_rl.return_value = instance
        
        instance.allow_request.return_value = True
        instance.get_wait_time.return_value = 0.0
        
        yield instance

@pytest.fixture
def mock_sanitizer():
    """Mock input sanitizer."""
    with patch('sanitizer.InputSanitizer') as mock_san:
        instance = Mock()
        mock_san.return_value = instance
        
        # Pass through sanitization
        instance.sanitize_text.side_effect = lambda x, **kwargs: x
        instance.sanitize_query.side_effect = lambda x: x
        instance.sanitize_filename.side_effect = lambda x: x
        instance.sanitize_metadata.side_effect = lambda x: x
        instance.validate_pdf_file.return_value = (True, "test.pdf")
        
        yield instance

@pytest.fixture
def analytics_fixture(temp_data_dir):
    """Create analytics instance for testing."""
    from analytics import AnalyticsDashboard
    
    log_file = temp_data_dir / "analytics.jsonl"
    dashboard = AnalyticsDashboard(str(log_file))
    
    # Add some sample data
    dashboard.log_query(
        query="test query 1",
        recall_success=True,
        latency_ms=45.2,
        results_count=5,
        source="context"
    )
    
    dashboard.log_query(
        query="test query 2",
        recall_success=False,
        latency_ms=120.5,
        results_count=0,
        source="llm_knowledge"
    )
    
    return dashboard

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # This would reset any global state
    yield
    # Cleanup after test

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit for UI testing."""
    with patch('streamlit.text_input') as mock_input:
        with patch('streamlit.button') as mock_button:
            with patch('streamlit.write') as mock_write:
                with patch('streamlit.success') as mock_success:
                    with patch('streamlit.error') as mock_error:
                        with patch('streamlit.spinner') as mock_spinner:
                            
                            # Configure mocks
                            mock_input.return_value = "test query"
                            mock_button.return_value = True
                            mock_spinner.return_value.__enter__ = Mock()
                            mock_spinner.return_value.__exit__ = Mock()
                            
                            yield {
                                'input': mock_input,
                                'button': mock_button,
                                'write': mock_write,
                                'success': mock_success,
                                'error': mock_error,
                                'spinner': mock_spinner
                            }

# Performance benchmark fixtures
@pytest.fixture
def benchmark_timer():
    """Simple timer for benchmarking."""
    class Timer:
        def __init__(self):
            self.times = []
        
        def __enter__(self):
            self.start = time.perf_counter()
            return self
        
        def __exit__(self, *args):
            self.times.append(time.perf_counter() - self.start)
        
        @property
        def avg(self):
            return sum(self.times) / len(self.times) if self.times else 0
        
        @property
        def total(self):
            return sum(self.times)
    
    return Timer()

# Test data generators
@pytest.fixture
def generate_test_documents():
    """Generate test documents for testing."""
    def _generate(count: int = 10) -> List[Dict[str, Any]]:
        docs = []
        for i in range(count):
            docs.append({
                "id": f"test-doc-{i}",
                "text": f"Test document {i} about cognitive AI and vector databases. "
                        f"This document contains information about {i % 3} topics.",
                "metadata": {
                    "source": f"test-{i}.pdf",
                    "page": i % 5 + 1,
                    "type": "test"
                }
            })
        return docs
    
    return _generate

@pytest.fixture
def mock_production_search():
    """Mock production search for testing."""
    with patch('production_search.ProductionAdvancedSearch') as mock_search:
        instance = Mock()
        mock_search.return_value = instance
        
        # Default search results
        instance.search.return_value = [
            ("doc1", "Cognitive AI content", {"source": "test"}),
            ("doc2", "Vector database content", {"source": "test"}),
            ("doc3", "Hybrid search content", {"source": "test"})
        ]
        
        yield instance
