#!/usr/bin/env python3
"""
OCR support for scanned PDFs using pytesseract
"""

import os
import tempfile
import platform
from typing import List, Optional
from io import BytesIO

try:
    import pytesseract
    from pdf2image import convert_from_bytes
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

def _configure_tesseract_path():
    """Configure Tesseract path on Windows if needed"""
    if platform.system() == "Windows" and OCR_AVAILABLE:
        tesseract_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break

def check_ocr_available():
    """Check if OCR dependencies are available"""
    if not OCR_AVAILABLE:
        missing = "pytesseract, pdf2image, or PIL"
        return False, f"Missing required packages: {missing}. Install with: pip install pytesseract pdf2image pillow"
    
    try:
        _configure_tesseract_path()
        
        # Check if Tesseract is installed
        try:
            version = pytesseract.get_tesseract_version()
            return True, f"OCR is available (Tesseract {version})"
        except Exception as e:
            return False, "Tesseract-OCR is not installed. Please install it from https://github.com/UB-Mannheim/tesseract/wiki"
    except ImportError as e:
        missing = str(e).split("'")[1] if "'" in str(e) else "required packages"
        return False, f"Missing Python package: {missing}. Run: pip install pytesseract pdf2image pillow"

def extract_text_with_ocr(pdf_bytes: bytes, progress_callback=None) -> List[str]:
    """
    Extract text from a scanned PDF using OCR
    
    Args:
        pdf_bytes: PDF file as bytes
        progress_callback: Optional callback for progress updates
        
    Returns:
        List of strings, one per page
    """
    if not OCR_AVAILABLE:
        raise ImportError("OCR dependencies not available. Install with: pip install pytesseract pdf2image pillow")
    
    try:
        _configure_tesseract_path()
        
        # Convert PDF pages to images
        if progress_callback:
            progress_callback("Converting PDF to images...")
        
        # Configure poppler path on Windows if needed
        poppler_path = None
        if platform.system() == "Windows":
            poppler_paths = [
                os.path.expanduser(r"~\AppData\Local\poppler\Library\bin"),
                r"C:\Program Files\poppler\Library\bin",
                r"C:\Program Files\poppler-24.08.0\Library\bin",
                r"C:\Program Files\poppler-23.11.0\Library\bin",
                r"C:\poppler\Library\bin",
            ]
            for path in poppler_paths:
                if os.path.exists(path):
                    poppler_path = path
                    break
        
        # Use lower DPI for faster processing (200 is usually good enough)
        if poppler_path:
            images = convert_from_bytes(pdf_bytes, dpi=200, poppler_path=poppler_path)
        else:
            images = convert_from_bytes(pdf_bytes, dpi=200)
        
        texts = []
        total_pages = len(images)
        
        for i, image in enumerate(images, 1):
            if progress_callback:
                progress_callback(f"Processing page {i}/{total_pages} with OCR...")
            
            try:
                # Perform OCR on the image
                text = pytesseract.image_to_string(image, lang='eng')
                texts.append(text)
            except Exception as e:
                texts.append("")  # Empty string for failed pages
                if progress_callback:
                    progress_callback(f"⚠️ OCR failed for page {i}: {str(e)}")
        
        return texts
        
    except Exception as e:
        raise Exception(f"OCR processing failed: {str(e)}")

def extract_text_with_ocr_from_file(pdf_path: str, progress_callback=None) -> List[str]:
    """
    Extract text from a scanned PDF file using OCR
    
    Args:
        pdf_path: Path to PDF file
        progress_callback: Optional callback for progress updates
        
    Returns:
        List of strings, one per page
    """
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    return extract_text_with_ocr(pdf_bytes, progress_callback)

if __name__ == "__main__":
    import sys
    
    # Check if OCR is available
    available, message = check_ocr_available()
    print(f"OCR Available: {available}")
    print(f"Message: {message}")
    
    if not available:
        print("\nTo enable OCR support:")
        print("1. Install Tesseract-OCR:")
        print("   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("   - Mac: brew install tesseract")
        print("   - Linux: sudo apt-get install tesseract-ocr")
        print("2. Install Python packages: pip install pytesseract pdf2image pillow")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"\nTesting OCR on: {pdf_path}")
        
        try:
            def progress(msg):
                print(f"  {msg}")
            
            texts = extract_text_with_ocr_from_file(pdf_path, progress)
            
            for i, text in enumerate(texts, 1):
                print(f"\n--- Page {i} ---")
                print(f"Extracted {len(text)} characters")
                if text:
                    print(f"First 200 chars: {text[:200]}...")
                    
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("\nUsage: python pdf_ocr.py <pdf_file>")