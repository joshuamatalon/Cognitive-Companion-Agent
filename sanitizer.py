"""
Input sanitization for security protection.
"""
import re
import html
from typing import Any, Dict, List, Optional
import unicodedata

class InputSanitizer:
    """Sanitize user inputs for security."""
    
    # Patterns for dangerous content
    SQL_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bOR\b.*=.*)",
        r"(';|\";\s*--)",
        r"(\bWAITFOR\b|\bDELAY\b)",
    ]
    
    SCRIPT_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"eval\s*\(",
        r"expression\s*\(",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.",
        r"\.\\",
        r"%2e%2e",
        r"%252e%252e",
    ]
    
    def __init__(self):
        self.max_text_length = 10000
        self.max_query_length = 500
        self.max_metadata_key_length = 100
        self.max_metadata_value_length = 1000
    
    def sanitize_text(self, text: str, max_length: Optional[int] = None) -> str:
        """Sanitize text input for storage."""
        if not text:
            return ""
        
        # Use provided max_length or default
        max_len = max_length or self.max_text_length
        
        # Truncate to max length
        text = text[:max_len]
        
        # Remove null bytes and control characters
        text = text.replace('\x00', '')
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\n\r\t')
        
        # HTML escape
        text = html.escape(text)
        
        # Remove potential SQL injection patterns
        for pattern in self.SQL_PATTERNS:
            text = re.sub(pattern, "[REMOVED]", text, flags=re.IGNORECASE)
        
        # Remove potential XSS patterns
        for pattern in self.SCRIPT_PATTERNS:
            text = re.sub(pattern, "[REMOVED]", text, flags=re.IGNORECASE)
        
        # Remove path traversal attempts
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
        # Normalize whitespace (preserve newlines for readability)
        lines = text.split('\n')
        normalized_lines = [' '.join(line.split()) for line in lines]
        text = '\n'.join(normalized_lines)
        
        return text.strip()
    
    def sanitize_query(self, query: str) -> str:
        """Sanitize search query input."""
        if not query:
            return ""
        
        # Limit query length
        query = query[:self.max_query_length]
        
        # Remove regex special characters that could break search
        query = re.sub(r'[\\^$*+?()[\]{}|]', ' ', query)
        
        # Remove SQL-like patterns
        for pattern in self.SQL_PATTERNS[:3]:  # Use only the most relevant patterns
            query = re.sub(pattern, "", query, flags=re.IGNORECASE)
        
        # Remove excessive whitespace
        query = ' '.join(query.split())
        
        # Remove quotes that might break query parsing
        query = query.replace('"', '').replace("'", '')
        
        return query.strip()
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        if not filename:
            return "unnamed"
        
        # Get base name without path
        import os
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
        
        # Remove path traversal patterns
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            filename = re.sub(pattern, "", filename, flags=re.IGNORECASE)
        
        # Limit length
        name, ext = os.path.splitext(filename)
        name = name[:100]
        ext = ext[:10]
        
        filename = name + ext
        
        # Default if empty after sanitization
        if not filename or filename == '.':
            filename = "unnamed"
        
        return filename
    
    def sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize metadata dictionary."""
        if not metadata:
            return {}
        
        clean_meta = {}
        
        # Limit number of metadata fields
        for key, value in list(metadata.items())[:50]:
            # Sanitize key
            clean_key = self.sanitize_text(str(key), max_length=self.max_metadata_key_length)
            clean_key = re.sub(r'[^\w\-_.]', '_', clean_key)  # Allow only safe characters in keys
            
            if not clean_key:
                continue
            
            # Sanitize value based on type
            if isinstance(value, str):
                clean_value = self.sanitize_text(value, max_length=self.max_metadata_value_length)
            elif isinstance(value, (int, float)):
                # Validate numeric ranges
                if isinstance(value, int):
                    clean_value = max(-2**31, min(2**31-1, value))
                else:
                    clean_value = float(max(-1e10, min(1e10, value)))
            elif isinstance(value, bool):
                clean_value = bool(value)
            elif isinstance(value, list):
                # Limit list size and sanitize elements
                clean_value = [
                    self.sanitize_text(str(item), max_length=200) 
                    for item in value[:20]
                ]
            elif isinstance(value, dict):
                # Recursive sanitization with depth limit
                if len(clean_meta) < 10:  # Prevent deep nesting
                    clean_value = self.sanitize_metadata(value)
                else:
                    clean_value = str(value)[:200]
            else:
                clean_value = self.sanitize_text(str(value), max_length=200)
            
            clean_meta[clean_key] = clean_value
        
        return clean_meta
    
    def validate_pdf_file(self, file_data: bytes, filename: str) -> tuple[bool, str]:
        """Validate PDF file for safety."""
        # Check file size (max 50MB)
        max_size = 50 * 1024 * 1024
        if len(file_data) > max_size:
            return False, "File too large (max 50MB)"
        
        # Check if it's actually a PDF
        if not file_data.startswith(b'%PDF'):
            return False, "Not a valid PDF file"
        
        # Check filename
        clean_name = self.sanitize_filename(filename)
        if not clean_name.lower().endswith('.pdf'):
            return False, "Invalid filename"
        
        return True, clean_name
    
    def is_safe_url(self, url: str) -> bool:
        """Check if URL is safe to fetch."""
        if not url:
            return False
        
        # Must start with http(s)
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Block local/internal addresses
        blocked_patterns = [
            r'localhost',
            r'127\.0\.0\.1',
            r'192\.168\.',
            r'10\.',
            r'172\.(1[6-9]|2[0-9]|3[0-1])\.',
            r'169\.254\.',
            r'::1',
            r'file://',
            r'ftp://',
        ]
        
        for pattern in blocked_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        return True

# Global sanitizer instance
sanitizer = InputSanitizer()
