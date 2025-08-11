import json
import re
from pathlib import Path
from datetime import datetime
from io import BytesIO

import streamlit as st
from pypdf import PdfReader

from memory_backend import (
    upsert_note,
    search_scores,
    delete_by_ids,
    export_all,
    reset_all,
    get_memory_stats,
)

# Configure page
st.set_page_config(
    page_title="Cognitive Companion", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Import professional fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* CSS Variables for theme support */
    :root {
        --background-color: rgba(255, 255, 255, 0.05);
        --secondary-background-color: rgba(255, 255, 255, 0.1);
        --border-color: rgba(255, 255, 255, 0.1);
        --text-color: var(--text-color);
        --primary-font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }
    
    /* Base font styling */
    .stApp {
        font-family: var(--primary-font);
    }
    
    /* Hide default Streamlit elements */
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    .stDecoration {display:none;}
    
    /* Main app styling */
    .main-header {
        padding: 2rem 0 1rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-family: var(--primary-font);
        font-size: 2.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .sub-header {
        text-align: center;
        color: #666;
        font-family: var(--primary-font);
        font-size: 1rem;
        font-weight: 400;
        margin-bottom: 2rem;
        letter-spacing: 0.01em;
    }
    
    /* Fixed section headers with proper contrast */
    .section-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 2rem 0 1.5rem 0;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.2);
        border: none;
    }
    
    .section-header h2 {
        color: white !important;
        margin: 0 !important;
        font-family: var(--primary-font);
        font-size: 1.25rem;
        font-weight: 500;
        letter-spacing: 0.01em;
    }
    
    /* Enhanced memory items */
    .memory-item {
        background: var(--background-color);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid var(--border-color);
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.2s ease;
    }
    
    .memory-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    }
    
    .memory-score {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .memory-id {
        font-family: 'Monaco', 'Menlo', monospace;
        background: var(--secondary-background-color);
        color: #495057;
        padding: 0.3rem 0.6rem;
        border-radius: 6px;
        font-size: 0.85rem;
        border: 1px solid #dee2e6;
    }
    
    /* Enhanced info boxes */
    .info-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #667eea;
        margin: 1.5rem 0;
        color: #37474f;
    }
    
    /* Enhanced sidebar */
    .sidebar .stSelectbox > div > div > select {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
    }
    
    /* Button enhancements */
    .stButton > button {
        border-radius: 8px;
        border: none;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Enhanced inputs */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e8ecf3;
        padding: 0.75rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #e8ecf3;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Enhanced expanders */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 0.5rem;
    }
    
    /* Custom metric styling */
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e8ecf3;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    
    /* Footer styling - dark mode friendly */
    .custom-footer {
        background: var(--background-color);
        padding: 2rem;
        border-radius: 15px;
        margin-top: 3rem;
        border: 1px solid var(--border-color);
    }
    
    /* Professional button styling */
    .stButton > button {
        font-family: var(--primary-font);
        font-weight: 500;
        font-size: 0.9rem;
        letter-spacing: 0.01em;
        transition: all 0.2s ease;
        border-radius: 6px;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Professional input styling */
    .stTextInput > div > div > input {
        font-family: var(--primary-font);
        font-size: 0.9rem;
        font-weight: 400;
    }
    
    .stSelectbox > div > div > select {
        font-family: var(--primary-font);
        font-size: 0.9rem;
        font-weight: 400;
    }
    
    .stNumberInput > div > div > input {
        font-family: var(--primary-font);
        font-size: 0.9rem;
        font-weight: 400;
    }
    
    /* Professional text elements */
    .stMarkdown {
        font-family: var(--primary-font);
    }
    
    .stCaption {
        font-family: var(--primary-font);
        font-size: 0.8rem;
        font-weight: 400;
        opacity: 0.7;
    }
</style>

""", unsafe_allow_html=True)

# Main header with system status indicator - properly centered
col_left, col_center, col_right = st.columns([1, 4, 1])

with col_left:
    # Empty space to balance the status indicator
    st.write("")
    
with col_center:
    # Truly centered header
    st.markdown('''
    <div style="text-align: center;">
        <h1 class="main-header">🧠 Cognitive Companion Agent</h1>
        <p class="sub-header">Your intelligent knowledge companion powered by AI</p>
    </div>
    ''', unsafe_allow_html=True)
    
with col_right:
    # Compact system status indicator
    st.markdown('''
    <div style="text-align: right; padding-top: 2rem;">
        <span style="background: linear-gradient(135deg, #28a745, #20c997); 
                     color: white; 
                     padding: 0.3rem 0.8rem; 
                     border-radius: 20px; 
                     font-size: 0.85rem;
                     display: inline-flex;
                     align-items: center;
                     gap: 0.3rem;
                     box-shadow: 0 2px 4px rgba(40, 167, 69, 0.2);">
            <span style="display: inline-block; width: 8px; height: 8px; 
                         background: white; border-radius: 50%; 
                         animation: pulse 2s infinite;"></span>
            System OK
        </span>
    </div>
    <style>
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
    ''', unsafe_allow_html=True)

# Initialize session state
if "hits" not in st.session_state:
    st.session_state.hits = []
if "query" not in st.session_state:
    st.session_state.query = ""
if "k" not in st.session_state:
    st.session_state.k = 5
if "deleted_memories" not in st.session_state:
    st.session_state.deleted_memories = []  # For undo functionality
if "search_history" not in st.session_state:
    st.session_state.search_history = []  # Track searches
if "reset_confirmation" not in st.session_state:
    st.session_state.reset_confirmation = False  # Track reset confirmation state
if "pdf_analysis" not in st.session_state:
    st.session_state.pdf_analysis = {}  # Cache PDF analysis results
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []  # Track Q&A conversations
if "sample_questions_used" not in st.session_state:
    st.session_state.sample_questions_used = False  # Track if user tried samples
if "current_question" not in st.session_state:
    st.session_state.current_question = ""  # Track current question input
if "is_followup" not in st.session_state:
    st.session_state.is_followup = False  # Track if current question is a follow-up

# PDF ingestion helper function with enhanced error handling
def _ingest_pdf_stream(file, name: str, chunk_chars: int = 1200, use_ocr: bool = False) -> int:
    """Process PDF with detailed progress and error handling."""
    try:
        # Reset file pointer to beginning (Streamlit files might not be at start)
        file.seek(0)
        
        # Read file bytes and create PdfReader from BytesIO for better reliability
        file_bytes = file.read()
        
        if not file_bytes:
            raise ValueError("Uploaded file appears to be empty (0 bytes)")
        
        reader = PdfReader(BytesIO(file_bytes))
        n = 0
        errors = []
        
        # Create progress containers
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            detail_text = st.empty()
        
        total_pages = len(reader.pages)
        
        if total_pages == 0:
            raise ValueError("PDF appears to be empty or corrupted")
        
        # Handle OCR processing if requested
        if use_ocr:
            try:
                from pdf_ocr import extract_text_with_ocr
                
                # Perform OCR
                with st.spinner("Performing OCR on scanned pages..."):
                    ocr_texts = extract_text_with_ocr(file_bytes, 
                        lambda msg: status_text.text(msg))
                
                # Process OCR results
                for pageno, text in enumerate(ocr_texts, 1):
                    if not text or len(text.strip()) < 3:
                        continue
                    
                    progress = pageno / len(ocr_texts)
                    progress_bar.progress(progress)
                    status_text.text(f"📄 Processing OCR text from page {pageno}...")
                    
                    # Clean and chunk the text
                    text = text.strip()
                    text = re.sub(r'[ \t]+', ' ', text)
                    text = re.sub(r'\n\s*\n', '\n\n', text)
                    
                    for off in range(0, len(text), chunk_chars):
                        piece = text[off : off + chunk_chars].strip()
                        if not piece:
                            continue
                        
                        try:
                            upsert_note(
                                piece,
                                {
                                    "source": name,
                                    "type": "pdf_ocr",
                                    "page": pageno,
                                    "chunk": off // chunk_chars,
                                    "timestamp": datetime.now().isoformat(),
                                },
                            )
                            n += 1
                        except Exception as e:
                            errors.append(f"OCR Page {pageno}, chunk {off//chunk_chars}: {str(e)}")
                
                # Return OCR results if successful
                if n > 0:
                    progress_bar.empty()
                    status_text.empty()
                    detail_text.empty()
                    return n
                    
            except Exception as e:
                st.error(f"OCR processing failed: {str(e)}")
                st.info("Falling back to regular text extraction...")
        
        # Process pages with detailed feedback
        for pageno, page in enumerate(reader.pages, start=1):
            try:
                progress = pageno / total_pages
                progress_bar.progress(progress)
                status_text.text(f"📄 Processing page {pageno} of {total_pages}...")
                
                # Extract text with multiple methods for better compatibility
                raw_text = None
                
                # Try standard text extraction
                try:
                    raw_text = page.extract_text()
                except Exception as e:
                    pass
                
                # If standard extraction returns empty, try alternative methods
                if not raw_text or len(raw_text.strip()) == 0:
                    try:
                        # Try extracting with layout mode (preserves more formatting)
                        raw_text = page.extract_text(extraction_mode="layout")
                    except:
                        pass
                
                # Check if text was extracted
                if not raw_text:
                    continue
                
                # Clean text while preserving content
                text = raw_text.strip()
                # Remove null bytes and excessive whitespace, but preserve structure
                text = text.replace('\x00', '').replace('\r\n', '\n').replace('\r', '\n')
                # Normalize multiple spaces and tabs, but keep line breaks
                text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
                text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
                
                if not text or len(text.strip()) < 3:
                    continue
                
                # Process chunks for this page
                page_chunks = 0
                
                for off in range(0, len(text), chunk_chars):
                    piece = text[off : off + chunk_chars].strip()
                    if not piece:
                        continue
                    
                    try:
                        upsert_note(
                            piece,
                            {
                                "source": name,
                                "type": "pdf",
                                "page": pageno,
                                "chunk": off // chunk_chars,
                                "timestamp": datetime.now().isoformat(),
                            },
                        )
                        n += 1
                        page_chunks += 1
                    except Exception as e:
                        errors.append(f"Page {pageno}, chunk {off//chunk_chars}: {str(e)}")
                
            except Exception as e:
                errors.append(f"Page {pageno}: {str(e)}")
                detail_text.error(f"❌ Error on page {pageno}: {str(e)}")
        
        # Clean up progress indicators
        progress_bar.empty()
        status_text.empty()
        detail_text.empty()
        
        # Report any errors
        if errors:
            with st.expander(f"⚠️ {len(errors)} errors occurred during processing"):
                for error in errors[:10]:  # Show first 10 errors
                    st.error(error)
                if len(errors) > 10:
                    st.info(f"... and {len(errors) - 10} more errors")
        
        return n
        
    except Exception as e:
        st.error(f"❌ Critical error processing PDF: {str(e)}")
        return 0

# Sidebar for data management
with st.sidebar:
    st.markdown("### 📚 Knowledge Management")
    
    # PDF Ingestion Section
    with st.expander("📄 PDF Ingestion", expanded=False):
        uploaded_file = st.file_uploader(
            "Upload a PDF document", 
            type=["pdf"],
            help="Upload PDFs to expand your knowledge base"
        )
        
        # Check if file is uploaded and analyze it
        use_ocr = False
        if uploaded_file is not None:
            file_key = f"{uploaded_file.name}_{uploaded_file.size if hasattr(uploaded_file, 'size') else 'unknown'}"
            
            # Check if we've already analyzed this file
            if file_key not in st.session_state.pdf_analysis:
                try:
                    from pdf_ocr import check_ocr_available
                    file_bytes = uploaded_file.read()
                    uploaded_file.seek(0)  # Reset file pointer
                    
                    reader = PdfReader(BytesIO(file_bytes))
                    is_likely_scanned = True
                    
                    # Quick check for text content
                    for i, page in enumerate(reader.pages[:min(3, len(reader.pages))]):
                        try:
                            test_text = page.extract_text()
                            if test_text and len(test_text.strip()) > 50:
                                is_likely_scanned = False
                                break
                        except:
                            pass
                    
                    # Cache the analysis
                    st.session_state.pdf_analysis[file_key] = {
                        'is_scanned': is_likely_scanned,
                        'pages': len(reader.pages)
                    }
                    
                except Exception as e:
                    st.warning(f"Could not analyze PDF: {str(e)}")
                    st.session_state.pdf_analysis[file_key] = {'is_scanned': False, 'pages': 0}
            
            # Use cached analysis
            analysis = st.session_state.pdf_analysis.get(file_key, {'is_scanned': False})
            
            if analysis['is_scanned']:
                st.warning("⚠️ This PDF appears to be scanned or image-based.")
                
                # Check OCR availability
                try:
                    from pdf_ocr import check_ocr_available
                    ocr_available, ocr_message = check_ocr_available()
                    if ocr_available:
                        use_ocr = st.checkbox("🔍 Use OCR to extract text from scanned pages", value=True, key=f"ocr_{file_key}")
                        if use_ocr:
                            st.info("💡 OCR processing may take longer depending on PDF size.")
                    else:
                        st.info(f"💡 {ocr_message}")
                        st.code("pip install pytesseract pdf2image pillow", language="bash")
                except ImportError:
                    st.info("💡 OCR support not available. To enable OCR for scanned PDFs:")
                    st.code("pip install pytesseract pdf2image pillow", language="bash")
                    st.info("Also install [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki)")
        
        col1, col2 = st.columns(2)
        with col1:
            chunk_size = st.slider(
                "Chunk Size", 
                min_value=800, 
                max_value=2000, 
                value=1200, 
                step=100,
                help="Size of text chunks for processing. Smaller chunks = more precise search, larger chunks = more context. 1200 is optimal for most documents."
            )
        with col2:
            if st.button("📥 Ingest PDF", type="primary", use_container_width=True):
                if uploaded_file is None:
                    st.warning("⚠️ Please select a PDF file first")
                else:
                    try:
                        with st.spinner("Processing PDF..."):
                            count = _ingest_pdf_stream(uploaded_file, uploaded_file.name, chunk_size, use_ocr)
                        st.success(f"✅ Successfully ingested {count} chunks from {uploaded_file.name}")
                    except Exception as e:
                        st.error(f"❌ PDF processing failed: {str(e)}")

    st.divider()
    
    # Manual Note Addition
    with st.expander("✏️ Add Knowledge", expanded=False):
        note_type = st.selectbox(
            "Knowledge Type",
            ["note", "fact", "goal", "task", "insight", "reference"],
            index=0,
            help="Categorize your knowledge for better organization"
        )
        
        note_content = st.text_area(
            "Content", 
            height=100, 
            placeholder="Enter your knowledge, insights, or facts...",
            max_chars=2000
        )
        
        if st.button("💾 Save Knowledge", type="primary", use_container_width=True):
            cleaned_content = note_content.strip()
            if cleaned_content:
                if len(cleaned_content) > 2000:
                    st.error("❌ Content too long! Maximum 2000 characters.")
                elif len(cleaned_content) < 5:
                    st.warning("⚠️ Content too short! Please write at least 5 characters.")
                else:
                    try:
                        note_id = upsert_note(cleaned_content, {"source": "manual", "type": note_type})
                        st.success(f"✅ Knowledge saved successfully!")
                        st.info(f"ID: `{note_id}`")
                    except Exception as e:
                        st.error(f"❌ Failed to save: {str(e)}")
            else:
                st.warning("⚠️ Please enter some content to save")

    st.divider()
    
    # System Management
    with st.expander("⚙️ System Management"):
        st.markdown("**🗄️ Memory Statistics**")
        
        # Get real memory statistics
        try:
            with st.spinner("Loading statistics..."):
                # Clear any potential caching and get fresh stats
                stats = get_memory_stats()
            
            if "error" in stats:
                st.error(f"⚠️ {stats['error']}")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Total Memories", 
                        stats.get("total_memories", 0),
                        help="Total number of knowledge chunks stored in your database"
                    )
                    st.metric(
                        "Recent Additions", 
                        stats.get("recent_upserts", 0),
                        help="Number of memories added in recent operations"
                    )
                with col2:
                    st.metric(
                        "Index Status", 
                        stats.get("index_status", "Unknown"),
                        help="Health status of your vector database index. 'Ready' means everything is working properly."
                    )
                    st.metric(
                        "Recent Deletions", 
                        stats.get("recent_deletes", 0),
                        help="Number of memories deleted in recent operations"
                    )
                
                # Technical details with helpful tooltips
                st.markdown("**🔧 Technical Details**")
                
                col_tech1, col_tech2 = st.columns([1, 3])
                with col_tech1:
                    st.write("**Index:**")
                with col_tech2:
                    st.write(f"{stats.get('index_name', 'N/A')}")
                    st.caption("💡 The name of your Pinecone vector database index")
                
                col_tech1, col_tech2 = st.columns([1, 3])
                with col_tech1:
                    st.write("**Model:**")
                with col_tech2:
                    st.write(f"{stats.get('embedding_model', 'N/A')}")
                    st.caption("💡 AI model used to convert text into searchable vectors")
                
                col_tech1, col_tech2 = st.columns([1, 3])
                with col_tech1:
                    st.write("**Dimensions:**")
                with col_tech2:
                    st.write(f"{stats.get('embedding_dimension', 'N/A')}")
                    st.caption("💡 Size of the vector space (higher = more detailed representation)")
        except Exception as e:
            st.error(f"Failed to load statistics: {str(e)}")
        
        st.markdown("**⚠️ Danger Zone**")
        
        # Handle reset confirmation with session state
        if not st.session_state.reset_confirmation:
            if st.button("🗑️ Reset All Memory", help="This will delete ALL stored knowledge", type="primary"):
                st.session_state.reset_confirmation = True
                st.rerun()
        else:
            st.warning("⚠️ This will permanently delete all your stored knowledge!")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Confirm Reset", type="secondary"):
                    try:
                        with st.spinner("Resetting memory... This may take 15-20 seconds"):
                            reset_all()
                        
                        # Clear all session state related to memories
                        st.session_state.hits = []
                        st.session_state.deleted_memories = []
                        st.session_state.search_history = []
                        st.session_state.reset_confirmation = False
                        
                        # Show success message
                        st.success("✅ Memory reset complete")
                        st.info("All memories have been permanently deleted from the vector database.")
                        
                        # Force a rerun to refresh all stats
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Reset failed: {str(e)}")
                        st.info("💡 Check your Pinecone API key and permissions.")
                        
                        # Show additional debug info
                        with st.expander("Debug Info"):
                            st.text(f"Error type: {type(e).__name__}")
                            st.text(f"Error details: {str(e)}")
                            
                            # Try to get current stats for debugging
                            try:
                                debug_stats = get_memory_stats()
                                st.json(debug_stats)
                            except:
                                st.text("Could not retrieve debug stats")
                        
                        # Reset confirmation state on error
                        st.session_state.reset_confirmation = False
                        
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state.reset_confirmation = False
                    st.info("Reset cancelled")
                    st.rerun()

# Main content area - streamlined without redundant header
# Question interface with sample questions
with st.container():
    question = st.text_input(
        "What would you like to know?",
        value=st.session_state.current_question,
        placeholder="Ask me anything about your knowledge...",
        help="🎯 Ask questions about your stored knowledge and documents",
        key="main_question_input"
    )
    
    # Show sample questions below the input if user is new
    if not st.session_state.sample_questions_used and not st.session_state.qa_history:
        st.info("💡 **New here?** Try one of these sample questions:")
        sample_questions = [
            "What are the key topics?",
            "Summarize my recent notes", 
            "Show me insights",
            "What should I review?"
        ]
        cols = st.columns(4)
        for idx, (col, question_text) in enumerate(zip(cols, sample_questions)):
            with col:
                if st.button(question_text, key=f"sample_{idx}", use_container_width=True):
                    st.session_state.sample_questions_used = True
                    st.session_state.current_question = question_text
                    st.rerun()
    
    # Balanced layout: prominent ask button with compact controls
    col_ask, col_controls = st.columns([5, 1.5])
    
    with col_ask:
        ask_button = st.button("🔍 Ask Companion", type="primary", use_container_width=True)
    
    with col_controls:
        # Sources selector with no visible label to match button height
        st.session_state.k = st.selectbox(
            "Sources",
            options=list(range(1, 11)),
            index=st.session_state.k - 1,
            help="🎯 Number of knowledge sources to use in answers",
            key="sources_selector",
            label_visibility="collapsed"
        )
        
        # Undo button with proper spacing
        if st.session_state.deleted_memories:
            if st.button("🔄 Undo Delete", help="Restore the most recently deleted memory", key="undo_button"):
                try:
                    deleted_item = st.session_state.deleted_memories.pop()
                    restored_id = upsert_note(deleted_item["text"], deleted_item["metadata"])
                    st.success(f"✅ Memory restored with new ID: {restored_id[:8]}...")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Undo failed: {str(e)}")
    
    if ask_button and question.strip():
        try:
            with st.spinner("🧠 Thinking..."):
                from rag_chain import answer
                
                # Check if this is a follow-up question
                is_followup = st.session_state.get('is_followup', False)
                
                if is_followup and st.session_state.qa_history:
                    # For follow-ups, provide context from the last Q&A
                    last_qa = st.session_state.qa_history[-1]
                    context_prompt = f"""Based on our previous conversation:

Q: {last_qa['question']}
A: {last_qa['answer']}

Now the user asks: {question.strip()}

Please provide a helpful response that builds upon the previous context."""
                    response, used_ids = answer(context_prompt, k=int(st.session_state.k))
                    # Reset the follow-up flag
                    st.session_state.is_followup = False
                else:
                    # Regular question processing
                    response, used_ids = answer(question.strip(), k=int(st.session_state.k))
            
            # Check if we got a valid response
            if not response or response.strip() == "":
                st.warning("🤔 I couldn't generate a response. This might mean:")
                st.markdown("""
                - Your question might be too vague
                - No relevant knowledge was found  
                - There might be an API issue
                
                **Try:** Being more specific or checking your knowledge base has relevant content.
                """)
            else:
                # Only show the answer and process if we got a valid response
                st.markdown("### 💡 Answer")
                st.write(response)
                
                # Save to conversation history
                st.session_state.qa_history.append({
                    "question": question.strip(),
                    "answer": response,
                    "sources": used_ids,
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })
                st.session_state.qa_history = st.session_state.qa_history[-10:]  # Keep last 10
                
                if used_ids:
                    with st.expander(f"📚 Sources Used ({len(used_ids)} memories)"):
                        st.write(f"**Memory IDs:** {', '.join([f'`{id}`' for id in used_ids])}")
                else:
                    st.info("📄 No specific sources were used for this answer.")
                
            # Clear the current question after successful processing
            st.session_state.current_question = ""
            
                    
        except Exception as e:
            st.error(f"❌ Error generating answer: {str(e)}")
            
            # If it's likely an empty database issue, provide guidance
            error_str = str(e).lower()
            if "empty" in error_str or "no" in error_str or "index" in error_str:
                st.info("💡 **Looks like your knowledge base might be empty!** Try adding some PDFs or notes first using the sidebar.")
            else:
                st.info("💡 Try checking your API keys in the environment or simplifying your question.")

# Show follow-up suggestions outside the main processing (if we have recent Q&A)
if st.session_state.qa_history:
    last_qa = st.session_state.qa_history[-1]
    
    # Only show follow-ups if the last question wasn't already a follow-up
    is_last_followup = any(phrase in last_qa['question'].lower() for phrase in [
        "tell me more", "key takeaways", "related notes", "expand on", "elaborate"
    ])
    
    if not is_last_followup:
        st.markdown("**💭 Continue the conversation:**")
        follow_cols = st.columns(3)
        
        # Simple follow-up prompts that build on context
        button_labels = ["Tell me more", "Key takeaways", "Related topics"]
        follow_questions = [
            "Can you tell me more about this?",
            "What are the key takeaways?", 
            "What related topics should I know about?"
        ]
        
        for idx, (col, label, question) in enumerate(zip(follow_cols, button_labels, follow_questions)):
            with col:
                if st.button(label, key=f"global_followup_{idx}", use_container_width=True):
                    st.session_state.current_question = question
                    st.session_state.is_followup = True  # Mark as follow-up
                    st.rerun()

st.divider()

# Memory Search and Management - Dropdown Style
with st.expander("🔍 Search Your Knowledge", expanded=bool(st.session_state.hits)):
    # Search interface
    with st.form("search_form", clear_on_submit=False):
        search_col1, search_col2, search_col3 = st.columns([3, 1, 1])
        
        with search_col1:
            # Dynamic placeholder based on search results
            if not st.session_state.hits:
                placeholder = "Search your knowledge base... (press / to focus)"
            else:
                placeholder = f"Search again... ({len(st.session_state.hits)} results from last search)"
            
            search_query = st.text_input(
                "Search your knowledge base", 
                value=st.session_state.query,
                placeholder=placeholder,
                help="🔍 Search through your knowledge base with keywords or questions",
                key="search_knowledge_input"
            )
        with search_col2:
            k_results = st.number_input("Results", min_value=1, max_value=20, value=int(st.session_state.k))
        with search_col3:
            search_submitted = st.form_submit_button("🔍 Search", type="primary", use_container_width=True)

    # Search history within the dropdown
    if st.session_state.search_history:
        st.markdown("**🕒 Recent Searches:**")
        recent_cols = st.columns(min(3, len(st.session_state.search_history[:6])))
        for i, (col, entry) in enumerate(zip(recent_cols, st.session_state.search_history[:6])):
            with col:
                if st.button(f"{entry['query'][:20]}...", key=f"recent_search_{i}", use_container_width=True):
                    st.session_state.query = entry['query']
                    st.rerun()
    
    # Show status within the dropdown
    if not st.session_state.hits:
        st.info("🔍 No search results yet. Try searching for topics, keywords, or questions above.")
    else:
        st.success(f"✅ Found {len(st.session_state.hits)} results for '{st.session_state.query}'")

    if search_submitted:
        st.session_state.query = search_query or "search"
        st.session_state.k = int(k_results)
        try:
            with st.spinner("🔍 Searching your knowledge base..."):
                st.session_state.hits = search_scores(st.session_state.query, k=int(k_results))
            
            # Save to search history (keep last 10 searches)
            search_entry = {
                "query": st.session_state.query,
                "timestamp": datetime.now().isoformat(),
                "results_count": len(st.session_state.hits)
            }
            st.session_state.search_history.insert(0, search_entry)
            st.session_state.search_history = st.session_state.search_history[:10]
            
            # Force rerun to show updated status and keep dropdown open
            st.rerun()
                
        except Exception as e:
            st.error(f"❌ Search failed: {str(e)}")
            st.info("💡 Try checking your API keys or simplifying your search query.")

# Display search results outside the dropdown
if st.session_state.hits:
    st.markdown(f"### 📋 Search Results ({len(st.session_state.hits)} found)")
    st.caption(f"Searched for: '{st.session_state.query}'")
    
    for i, (memory_id, content, metadata, score) in enumerate(st.session_state.hits, 1):
        with st.container():
            st.markdown(f"""
            <div class="memory-item">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span><strong>#{i}</strong> <span class="memory-id">{memory_id}</span></span>
                    <span class="memory-score">Score: {score:.3f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Content preview
            preview_length = 300
            content_preview = content[:preview_length] + "..." if len(content) > preview_length else content
            st.write(content_preview)
            
            # Metadata and actions
            col_meta, col_actions = st.columns([3, 1])
            with col_meta:
                if metadata:
                    meta_text = " • ".join([f"{k}: {v}" for k, v in metadata.items() if k != "text"])
                    st.caption(f"📊 {meta_text}")
            
            with col_actions:
                if st.button(f"🗑️ Delete", key=f"del_{memory_id}", help="Delete this memory"):
                    try:
                        # Store memory for undo before deleting
                        memory_data = {
                            "id": memory_id,
                            "text": content,
                            "metadata": metadata,
                            "deleted_at": datetime.now().isoformat()
                        }
                        st.session_state.deleted_memories.append(memory_data)
                        
                        # Keep only last 5 deleted memories
                        if len(st.session_state.deleted_memories) > 5:
                            st.session_state.deleted_memories.pop(0)
                        
                        # Perform the deletion
                        with st.spinner("Deleting memory..."):
                            delete_by_ids([memory_id])
                        
                        st.session_state.hits = [h for h in st.session_state.hits if h[0] != memory_id]
                        st.success("✅ Memory deleted (undo available)")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Delete failed: {str(e)}")

# Add a clear results button if we have results
if st.session_state.hits:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🧙 Clear Search Results", use_container_width=True):
            st.session_state.hits = []
            st.session_state.query = ""
            st.success("✅ Search results cleared")
            st.rerun()
            
            st.divider()

# Show conversation history if available
if st.session_state.qa_history:
    with st.expander(f"💬 Conversation History ({len(st.session_state.qa_history)} exchanges)", expanded=False):
        for qa in reversed(st.session_state.qa_history[-5:]):  # Show last 5, newest first
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**Q:** {qa['question']}")
                answer_preview = (qa['answer'][:120] + "...") if len(qa['answer']) > 120 else qa['answer']
                st.markdown(f"**A:** {answer_preview}")
            with col2:
                st.caption(qa['timestamp'])
                if qa['sources']:
                    st.caption(f"{len(qa['sources'])} sources")
            st.divider()

# Recent Activity Section - Now collapsible
with st.expander("📜 Recent Activity", expanded=False):
    def _tail_log(n: int = 10):
        try:
            lines = Path("data/memory_log.jsonl").read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return []
        out = []
        for line in lines[-n:][::-1]:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
        return out
    
    logs = _tail_log(10)
    if logs:
        for i, entry in enumerate(logs[:5]):  # Show only last 5 entries
            event = entry.get("event", "unknown")
            entry_id = entry.get("id")
            meta = entry.get("meta", {})
            
            if event == "upsert" and entry_id:
                col_log, col_action = st.columns([4, 1])
                with col_log:
                    st.write(f"📝 **Added** knowledge • Type: `{meta.get('type', 'unknown')}` • Length: {entry.get('len', 0)} chars")
                    st.caption(f"ID: `{entry_id}`")
                with col_action:
                    if st.button(f"🗑️", key=f"logdel_{entry_id}_{i}", help="Delete this entry"):
                        try:
                            delete_by_ids([entry_id])
                            st.success("Entry deleted")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Delete failed: {e}")
            elif event == "delete":
                st.write(f"🗑️ **Deleted** memories • IDs: {entry.get('ids', [])}")
    else:
        st.info("📭 No recent activity. Start adding knowledge to see activity here.")

# Export functionality
with st.expander("📤 Export Knowledge Base"):
    st.markdown("Download your entire knowledge base as JSON for backup or analysis.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("📊 Preview Export", type="secondary"):
            try:
                with st.spinner("Generating preview..."):
                    export_data = export_all()
                
                if export_data:
                    st.success(f"✅ Found {len(export_data)} memories to export")
                    
                    # Show preview of first few items
                    st.markdown("**Preview (first 3 items):**")
                    for i, item in enumerate(export_data[:3]):
                        with st.container():
                            st.write(f"**{i+1}.** `{item.get('id', 'N/A')[:8]}...`")
                            preview_text = item.get('text', '')[:100]
                            st.write(f"Text: {preview_text}..." if len(preview_text) == 100 else f"Text: {preview_text}")
                            if item.get('metadata'):
                                st.caption(f"Metadata: {item['metadata']}")
                            st.divider()
                else:
                    st.warning("⚠️ No memories found to export")
                    
            except Exception as e:
                st.error(f"❌ Preview failed: {str(e)}")
    
    with col2:
        if st.button("💾 Download Export", type="primary"):
            try:
                with st.spinner("Preparing download..."):
                    export_data = export_all()
                
                if export_data:
                    # Add export metadata
                    export_package = {
                        "export_info": {
                            "timestamp": datetime.now().isoformat(),
                            "total_memories": len(export_data),
                            "version": "1.1"
                        },
                        "memories": export_data
                    }
                    
                    st.download_button(
                        label="📥 Download JSON File",
                        data=json.dumps(export_package, indent=2, ensure_ascii=False),
                        file_name=f"cognitive_companion_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        type="primary"
                    )
                    st.success(f"✅ Ready to download {len(export_data)} memories!")
                else:
                    st.warning("⚠️ No data available for export. Add some knowledge first!")
                    
            except Exception as e:
                st.error(f"❌ Export preparation failed: {str(e)}")

# Enhanced Footer
st.markdown('''
<div class="custom-footer">
    <div style="text-align: center;">
        <h3 style="color: #667eea; margin-bottom: 1rem; font-family: var(--primary-font); font-weight: 500; font-size: 1.5rem;">🧠 Cognitive Companion Agent</h3>
        <p style="color: #666; margin-bottom: 1rem; font-family: var(--primary-font); font-size: 0.9rem; font-weight: 400;">
            <strong style="font-weight: 500;">Version 1.2</strong> • Powered by OpenAI & Pinecone
        </p>
        <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
            <span style="color: #667eea; font-family: var(--primary-font); font-size: 0.85rem; font-weight: 400;">📚 Knowledge Management</span>
            <span style="color: #667eea; font-family: var(--primary-font); font-size: 0.85rem; font-weight: 400;">🔍 Intelligent Search</span>
            <span style="color: #667eea; font-family: var(--primary-font); font-size: 0.85rem; font-weight: 400;">💬 AI-Powered Answers</span>
        </div>
        <p style="margin-top: 1rem; font-size: 0.9rem; color: #999;">
            Built with ❤️ for intelligent knowledge interaction
        </p>
    </div>
</div>
''', unsafe_allow_html=True)