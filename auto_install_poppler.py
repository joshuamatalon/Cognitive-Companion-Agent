#!/usr/bin/env python3
"""
Automatically download and set up Poppler for Windows
"""

import os
import sys
import io

# Fix Unicode output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import zipfile
import urllib.request
import shutil
from pathlib import Path

def download_and_install_poppler():
    """Download and install Poppler for Windows"""
    
    # Poppler download URL (using a stable release)
    poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"
    
    # Target directory
    target_dir = Path(r"C:\Program Files\poppler")
    temp_zip = Path("poppler_temp.zip")
    temp_extract = Path("poppler_temp")
    
    try:
        # Check if already installed
        if (target_dir / "Library" / "bin" / "pdftoppm.exe").exists():
            print("Poppler is already installed!")
            return True
        
        print("Downloading Poppler for Windows...")
        print(f"   From: {poppler_url}")
        
        # Download the file
        urllib.request.urlretrieve(poppler_url, temp_zip)
        print(f"Downloaded {temp_zip.stat().st_size / 1024 / 1024:.1f} MB")
        
        # Extract the zip
        print("Extracting Poppler...")
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(temp_extract)
        
        # Find the extracted folder (it's usually named poppler-xx.xx.x)
        extracted_folders = list(temp_extract.glob("poppler-*"))
        if not extracted_folders:
            print("[ERROR] Error: Could not find extracted poppler folder")
            return False
        
        source_dir = extracted_folders[0]
        
        # Create target directory if it doesn't exist
        print(f"[DIR] Installing to: {target_dir}")
        
        # Try to create the directory (might need admin rights)
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            print("[ERROR] Permission denied. Trying user directory instead...")
            target_dir = Path.home() / "AppData" / "Local" / "poppler"
            target_dir.mkdir(parents=True, exist_ok=True)
            print(f"[DIR] Installing to user directory: {target_dir}")
        
        # Copy files
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        shutil.copytree(source_dir, target_dir)
        
        print("[OK] Poppler installed successfully!")
        print(f"   Location: {target_dir}")
        
        # Test installation
        pdftoppm_path = target_dir / "Library" / "bin" / "pdftoppm.exe"
        if pdftoppm_path.exists():
            print("[OK] Installation verified: pdftoppm.exe found")
            
            # Update pdf_ocr.py to include this path
            update_pdf_ocr_with_path(str(target_dir / "Library" / "bin"))
            return True
        else:
            print("[ERROR] Warning: pdftoppm.exe not found in expected location")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error installing Poppler: {e}")
        return False
        
    finally:
        # Clean up temp files
        if temp_zip.exists():
            temp_zip.unlink()
        if temp_extract.exists():
            shutil.rmtree(temp_extract, ignore_errors=True)

def update_pdf_ocr_with_path(poppler_bin_path):
    """Update pdf_ocr.py to include the new poppler path"""
    pdf_ocr_path = Path("pdf_ocr.py")
    
    if not pdf_ocr_path.exists():
        return
    
    content = pdf_ocr_path.read_text()
    
    # Check if path already exists
    if poppler_bin_path in content:
        print(f"[INFO] Path already in pdf_ocr.py: {poppler_bin_path}")
        return
    
    # Add the path to the poppler_paths list
    search_str = 'poppler_paths = ['
    if search_str in content:
        # Insert the new path at the beginning of the list
        new_path_line = f'                r"{poppler_bin_path}",'
        content = content.replace(
            search_str + '\n',
            search_str + '\n' + new_path_line + '\n'
        )
        pdf_ocr_path.write_text(content)
        print(f"[OK] Added {poppler_bin_path} to pdf_ocr.py")

if __name__ == "__main__":
    print("=== Poppler Auto-Installer for Windows ===")
    print()
    
    success = download_and_install_poppler()
    
    if success:
        print()
        print("[SUCCESS] Poppler is ready to use!")
        print("   You can now use OCR with scanned PDFs in the app.")
    else:
        print()
        print("[WARNING] Poppler installation had issues.")
        print("   You may need to install it manually from:")
        print("   https://github.com/oschwartz10612/poppler-windows/releases/")
    
    input("\nPress Enter to exit...")