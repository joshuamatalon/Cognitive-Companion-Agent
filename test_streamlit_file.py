#!/usr/bin/env python3
"""
Test script to understand Streamlit file upload behavior
"""

from pypdf import PdfReader
from io import BytesIO
import streamlit as st

def test_streamlit_file_upload():
    """Test how Streamlit file upload works with PdfReader"""
    
    st.write("# PDF Upload Test")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        st.write(f"File name: {uploaded_file.name}")
        st.write(f"File type: {type(uploaded_file)}")
        st.write(f"File size: {uploaded_file.size if hasattr(uploaded_file, 'size') else 'Unknown'}")
        
        # Test different ways to read the file
        try:
            # Method 1: Direct to PdfReader (what we're currently doing)
            st.write("### Method 1: Direct to PdfReader")
            reader1 = PdfReader(uploaded_file)
            st.write(f"✅ Direct method works: {len(reader1.pages)} pages")
            
            # Reset file pointer
            uploaded_file.seek(0)
            
            # Method 2: Via BytesIO (more robust)
            st.write("### Method 2: Via BytesIO")
            file_bytes = uploaded_file.read()
            st.write(f"Read {len(file_bytes)} bytes")
            reader2 = PdfReader(BytesIO(file_bytes))
            st.write(f"✅ BytesIO method works: {len(reader2.pages)} pages")
            
            # Test text extraction from first page
            if len(reader2.pages) > 0:
                st.write("### Text Extraction Test")
                first_page = reader2.pages[0]
                raw_text = first_page.extract_text()
                st.write(f"Raw text length: {len(raw_text) if raw_text else 0}")
                if raw_text:
                    st.write(f"First 200 chars: {repr(raw_text[:200])}")
                else:
                    st.write("❌ No text extracted from first page")
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

if __name__ == "__main__":
    test_streamlit_file_upload()