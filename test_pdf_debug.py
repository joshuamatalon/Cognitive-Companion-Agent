#!/usr/bin/env python3
"""
Debug script to test PDF ingestion and identify the empty document issue.
"""

from pypdf import PdfReader
from io import BytesIO
import sys
import os

def test_pdf_reader(pdf_path=None):
    """Test PDF reading functionality with detailed debugging."""
    
    if pdf_path and os.path.exists(pdf_path):
        print(f"Testing PDF file: {pdf_path}")
        try:
            with open(pdf_path, 'rb') as f:
                file_bytes = f.read()
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return False
    else:
        print("No PDF file provided - creating a test scenario")
        return False
    
    try:
        # Test PdfReader with BytesIO (same as Streamlit file upload)
        reader = PdfReader(BytesIO(file_bytes))
        
        print(f"✅ PDF opened successfully")
        print(f"📄 Total pages: {len(reader.pages)}")
        
        if len(reader.pages) == 0:
            print("❌ PDF appears to have 0 pages")
            return False
        
        # Test text extraction from first few pages
        for i, page in enumerate(reader.pages[:3]):  # Check first 3 pages
            try:
                raw_text = page.extract_text()
                print(f"\n--- Page {i+1} ---")
                print(f"Raw text length: {len(raw_text) if raw_text else 0}")
                print(f"Raw text type: {type(raw_text)}")
                
                if raw_text:
                    # Test the NEW processing logic from app.py
                    text = raw_text.strip()
                    # Remove null bytes and excessive whitespace, but preserve structure
                    text = text.replace('\x00', '').replace('\r\n', '\n').replace('\r', '\n')
                    # Normalize multiple spaces and tabs, but keep line breaks
                    import re
                    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
                    text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
                    
                    print(f"Processed text length: {len(text)}")
                    print(f"Text content sufficient: {len(text.strip()) >= 3}")
                    print(f"First 200 chars: {repr(text[:200])}")
                    
                    if not text or len(text.strip()) < 3:
                        print(f"❌ Text insufficient after processing! (length: {len(text.strip()) if text else 0})")
                    else:
                        print("✅ Text processing successful")
                else:
                    print("❌ No text extracted from page")
                    
            except Exception as e:
                print(f"❌ Error extracting text from page {i+1}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error opening PDF: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        test_pdf_reader(pdf_path)
    else:
        print("Usage: python test_pdf_debug.py <path_to_pdf>")
        print("This script will help debug PDF ingestion issues.")