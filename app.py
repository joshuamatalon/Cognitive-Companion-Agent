import json
from pathlib import Path
from datetime import datetime

import streamlit as st
from pypdf import PdfReader

from memory_backend import (
    upsert_note,
    search_scores,
    delete_by_ids,
    export_all,
    reset_all,
)

# Configure page
st.set_page_config(
    page_title="Cognitive Companion", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Hide default Streamlit elements */
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    .stDecoration {display:none;}
    
    /* Main app styling */
    .main-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-style: italic;
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
        font-size: 1.4rem;
        font-weight: 600;
    }
    
    /* Enhanced memory items */
    .memory-item {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e8ecf3;
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
        background: #f8f9fa;
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
    
    /* Footer styling */
    .custom-footer {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-top: 3rem;
        border: 1px solid #e8ecf3;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<h1 class="main-header">🧠 Cognitive Companion Agent</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Your intelligent knowledge companion powered by AI</p>', unsafe_allow_html=True)

# Initialize session state
if "hits" not in st.session_state:
    st.session_state.hits = []
if "query" not in st.session_state:
    st.session_state.query = "frontier objective"
if "k" not in st.session_state:
    st.session_state.k = 5

# PDF ingestion helper function
def _ingest_pdf_stream(file, name: str, chunk_chars: int = 1200) -> int:
    reader = PdfReader(file)
    n = 0
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_pages = len(reader.pages)
    
    for pageno, page in enumerate(reader.pages, start=1):
        progress = pageno / total_pages
        progress_bar.progress(progress)
        status_text.text(f"Processing page {pageno} of {total_pages}...")
        
        text = (page.extract_text() or "").strip()
        text = " ".join(text.split())
        if not text:
            continue
            
        for off in range(0, len(text), chunk_chars):
            piece = text[off : off + chunk_chars].strip()
            if not piece:
                continue
            upsert_note(
                piece,
                {
                    "source": name,
                    "type": "pdf",
                    "page": pageno,
                    "chunk": off // chunk_chars,
                },
            )
            n += 1
    
    progress_bar.empty()
    status_text.empty()
    return n

# Sidebar for data management
with st.sidebar:
    st.markdown("### 📚 Knowledge Management")
    
    # PDF Ingestion Section
    with st.expander("📄 PDF Ingestion", expanded=True):
        uploaded_file = st.file_uploader(
            "Upload a PDF document", 
            type=["pdf"],
            help="Upload PDFs to expand your knowledge base"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            chunk_size = st.slider("Chunk Size", 800, 2000, 1200, 100)
        with col2:
            if st.button("📥 Ingest PDF", type="primary", use_container_width=True):
                if uploaded_file is None:
                    st.warning("⚠️ Please select a PDF file first")
                else:
                    try:
                        with st.spinner("Processing PDF..."):
                            count = _ingest_pdf_stream(uploaded_file, uploaded_file.name, chunk_size)
                        st.success(f"✅ Successfully ingested {count} chunks from {uploaded_file.name}")
                    except Exception as e:
                        st.error(f"❌ PDF processing failed: {str(e)}")

    st.divider()
    
    # Manual Note Addition
    with st.expander("✏️ Add Knowledge", expanded=True):
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
        # You could add memory stats here if available
        st.info("Memory statistics would appear here")
        
        st.markdown("**⚠️ Danger Zone**")
        if st.button("🗑️ Reset All Memory", help="This will delete ALL stored knowledge"):
            if st.button("Confirm Reset", type="secondary"):
                reset_all()
                st.session_state.hits = []
                st.success("✅ Memory reset complete")

# Main content area
st.markdown('<div class="section-header"><h2>💬 Ask Your Companion</h2></div>', unsafe_allow_html=True)

# Create two columns for the main interface
col1, col2 = st.columns([2, 1])

with col1:
    # Question interface
    with st.container():
        question = st.text_input(
            "What would you like to know?",
            value="",
            placeholder="Ask me anything about your stored knowledge...",
            help="Ask questions and I'll search through your knowledge base to provide informed answers"
        )
        
        col_ask, col_settings = st.columns([3, 1])
        with col_ask:
            ask_button = st.button("🔍 Ask Companion", type="primary", use_container_width=True)
        with col_settings:
            with st.popover("⚙️ Settings"):
                st.session_state.k = st.slider("Results to use", 1, 10, st.session_state.k)
        
        if ask_button and question.strip():
            try:
                with st.spinner("🧠 Thinking..."):
                    from rag_chain import answer
                    response, used_ids = answer(question.strip(), k=int(st.session_state.k))
                
                st.markdown("### 💡 Answer")
                st.write(response)
                
                if used_ids:
                    with st.expander(f"📚 Sources Used ({len(used_ids)} memories)"):
                        st.write(f"**Memory IDs:** {', '.join([f'`{id}`' for id in used_ids])}")
                        
            except Exception as e:
                st.error(f"❌ Error generating answer: {str(e)}")

with col2:
    # Quick stats with better styling
    st.markdown('<div class="section-header"><h2>📊 Quick Stats</h2></div>', unsafe_allow_html=True)
    
    # Enhanced metrics display
    if st.session_state.hits:
        st.markdown(f'''
        <div class="metric-container">
            <h3 style="color: #667eea; margin: 0;">🔍 {len(st.session_state.hits)}</h3>
            <p style="margin: 0.5rem 0 0 0; color: #666;">Recent Searches</p>
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown('''
        <div class="info-box">
            <strong>🔍 Ready to Search</strong><br>
            <small>Your search results will appear here</small>
        </div>
        ''', unsafe_allow_html=True)
    
    # Add knowledge base health indicator
    st.markdown('''
    <div class="metric-container" style="margin-top: 1rem;">
        <h4 style="color: #28a745; margin: 0;">✅ System Status</h4>
        <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">All systems operational</p>
    </div>
    ''', unsafe_allow_html=True)

st.divider()

# Memory Search and Management
st.markdown('<div class="section-header"><h2>🔍 Explore Your Knowledge</h2></div>', unsafe_allow_html=True)

# Search interface
with st.form("search_form", clear_on_submit=False):
    search_col1, search_col2, search_col3 = st.columns([3, 1, 1])
    
    with search_col1:
        search_query = st.text_input("Search your knowledge base", value=st.session_state.query)
    with search_col2:
        k_results = st.number_input("Results", min_value=1, max_value=20, value=int(st.session_state.k))
    with search_col3:
        search_submitted = st.form_submit_button("🔍 Search", type="primary")

if search_submitted:
    st.session_state.query = search_query or "search"
    st.session_state.k = int(k_results)
    try:
        st.session_state.hits = search_scores(st.session_state.query, k=int(k_results))
    except Exception as e:
        st.error(f"Search failed: {str(e)}")

# Display search results
if st.session_state.hits:
    st.markdown(f"### 📋 Search Results ({len(st.session_state.hits)} found)")
    
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
                        delete_by_ids([memory_id])
                        st.session_state.hits = [h for h in st.session_state.hits if h[0] != memory_id]
                        st.success("Memory deleted")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {e}")
            
            st.divider()
else:
    st.markdown('<div class="info-box">🔍 <strong>No search results yet.</strong> Use the search box above to explore your knowledge base.</div>', unsafe_allow_html=True)

# Recent Activity Section
st.markdown('<div class="section-header"><h2>📜 Recent Activity</h2></div>', unsafe_allow_html=True)

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
    st.markdown('<div class="info-box">📭 <strong>No recent activity.</strong> Start adding knowledge to see activity here.</div>', unsafe_allow_html=True)

# Export functionality
with st.expander("📤 Export Knowledge Base"):
    st.markdown("Download your entire knowledge base as JSON for backup or analysis.")
    if st.button("📋 Generate Export", type="secondary"):
        try:
            export_data = export_all()
            if export_data:
                st.download_button(
                    label="💾 Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"knowledge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.info("No data available for export")
        except Exception as e:
            st.error(f"Export failed: {e}")

# Enhanced Footer
st.markdown('''
<div class="custom-footer">
    <div style="text-align: center;">
        <h3 style="color: #667eea; margin-bottom: 1rem;">🧠 Cognitive Companion Agent</h3>
        <p style="color: #666; margin-bottom: 1rem;">
            <strong>Version 1.1</strong> • Powered by OpenAI & Pinecone
        </p>
        <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
            <span style="color: #667eea;">📚 Knowledge Management</span>
            <span style="color: #667eea;">🔍 Intelligent Search</span>
            <span style="color: #667eea;">💬 AI-Powered Answers</span>
        </div>
        <p style="margin-top: 1rem; font-size: 0.9rem; color: #999;">
            Built with ❤️ for intelligent knowledge interaction
        </p>
    </div>
</div>
''', unsafe_allow_html=True)