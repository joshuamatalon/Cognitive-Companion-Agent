#!/usr/bin/env python3
"""
Direct test of pypdf text extraction to diagnose PDF issues
"""

from pypdf import PdfReader
import sys
import os

def test_pdf_extraction(pdf_path):
    """Test various PDF extraction methods"""
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    print(f"Testing PDF: {pdf_path}")
    print(f"File size: {os.path.getsize(pdf_path)} bytes")
    print("-" * 50)
    
    try:
        # Open the PDF
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            
            print(f"✅ PDF opened successfully")
            print(f"Total pages: {len(reader.pages)}")
            print(f"Is encrypted: {reader.is_encrypted}")
            
            # Get PDF metadata
            if reader.metadata:
                print("\nMetadata:")
                for key, value in reader.metadata.items():
                    print(f"  {key}: {value}")
            
            print("\n" + "=" * 50)
            
            # Test each page
            for i, page in enumerate(reader.pages[:5], 1):  # Test first 5 pages
                print(f"\n--- Page {i} ---")
                
                # Method 1: Standard extraction
                try:
                    text1 = page.extract_text()
                    if text1:
                        print(f"Standard extraction: {len(text1)} chars")
                        print(f"First 200 chars: {repr(text1[:200])}")
                    else:
                        print("Standard extraction: No text extracted")
                except Exception as e:
                    print(f"Standard extraction failed: {e}")
                
                # Method 2: Layout mode
                try:
                    text2 = page.extract_text(extraction_mode="layout")
                    if text2:
                        print(f"Layout extraction: {len(text2)} chars")
                    else:
                        print("Layout extraction: No text extracted")
                except Exception as e:
                    print(f"Layout extraction failed: {e}")
                
                # Check for images
                try:
                    if hasattr(page, 'images'):
                        image_count = len(list(page.images))
                        if image_count > 0:
                            print(f"Page contains {image_count} images")
                except:
                    pass
                
                # Check page size
                try:
                    mediabox = page.mediabox
                    print(f"Page size: {float(mediabox.width)} x {float(mediabox.height)}")
                except:
                    pass
            
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_pdf_extraction(sys.argv[1])
    else:
        print("Usage: python test_pypdf_direct.py <path_to_pdf>")
        print("\nThis will test different text extraction methods on your PDF.")