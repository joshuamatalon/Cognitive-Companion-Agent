"""
BM25 keyword search to complement vector search.
Provides exact keyword matching for numbers, IDs, specific terms.
"""

import re
import json
import sqlite3
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# Try to import BM25 and NLTK, but provide fallback if not available
try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False
    print("Warning: rank-bm25 not installed. Keyword search will be disabled.")
    print("Install with: pip install rank-bm25")

try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False
    print("Warning: NLTK not installed. Using basic tokenization.")
    print("Install with: pip install nltk")

# Download NLTK data if not present (only if NLTK is available)
if HAS_NLTK:
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
        except:
            pass
        try:
            nltk.download('punkt_tab', quiet=True)
        except:
            pass
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        try:
            nltk.download('stopwords', quiet=True)
        except:
            pass


class KeywordSearchIndex:
    """BM25-based keyword search index with SQLite persistence."""
    
    def __init__(self, db_path: str = "cognitive_companion.db"):
        """Initialize keyword search with SQLite backend."""
        self.enabled = HAS_BM25  # Track if keyword search is available
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Get English stop words first (before any other operations)
        if HAS_NLTK:
            try:
                self.stop_words = set(stopwords.words('english'))
            except:
                # Fallback stop words if NLTK fails
                self.stop_words = {
                    'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were',
                    'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                    'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need'
                }
        else:
            # Basic stop words when NLTK not available
            self.stop_words = {
                'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were',
                'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need'
            }
        
        # Create documents table if not exists
        self._create_tables()
        
        # Load existing documents and build BM25 index only if available
        if self.enabled:
            self._rebuild_index()
        else:
            self.bm25 = None
            self.doc_ids = []
            self.doc_contents = []
    
    def _create_tables(self):
        """Create documents table for keyword search."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25, preserving important patterns."""
        if not text:
            return []
        
        # Convert to lowercase
        text_lower = text.lower()
        
        # Extract special patterns that should be preserved
        special_tokens = []
        
        # Dollar amounts (e.g., $2,100)
        dollar_pattern = r'\$[\d,]+(?:\.\d{2})?'
        special_tokens.extend(re.findall(dollar_pattern, text))
        
        # Percentages (e.g., 91.7%)
        percent_pattern = r'\d+(?:\.\d+)?%'
        special_tokens.extend(re.findall(percent_pattern, text))
        
        # IDs and codes (e.g., ABC-123, ID-456)
        id_pattern = r'\b[A-Z]+-\d+\b'
        special_tokens.extend(re.findall(id_pattern, text, re.IGNORECASE))
        
        # Date ranges (e.g., 18-24 months)
        date_pattern = r'\d+[-–]\d+\s*(?:month|year|week|day)s?'
        special_tokens.extend(re.findall(date_pattern, text, re.IGNORECASE))
        
        # Regular tokenization
        if HAS_NLTK:
            try:
                tokens = word_tokenize(text_lower)
            except:
                # Fallback tokenization
                tokens = text_lower.split()
        else:
            # Basic tokenization when NLTK not available
            tokens = text_lower.split()
        
        # Remove stop words but keep numbers and special characters
        filtered_tokens = []
        for token in tokens:
            # Keep numbers, special tokens, and non-stop words
            if (token not in self.stop_words or 
                token.replace('.', '').replace(',', '').isdigit() or
                '$' in token or '%' in token or '-' in token):
                filtered_tokens.append(token)
        
        # Add special tokens (already lowercase)
        filtered_tokens.extend([t.lower() for t in special_tokens])
        
        return filtered_tokens
    
    def _rebuild_index(self):
        """Rebuild BM25 index from database."""
        if not self.enabled:
            return
            
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, content FROM documents")
        rows = cursor.fetchall()
        
        self.doc_ids = []
        self.doc_contents = []
        tokenized_docs = []
        
        for row in rows:
            self.doc_ids.append(row['id'])
            self.doc_contents.append(row['content'])
            tokenized_docs.append(self._tokenize(row['content']))
        
        # Build BM25 index
        if tokenized_docs and HAS_BM25:
            self.bm25 = BM25Okapi(tokenized_docs)
        else:
            self.bm25 = None
    
    def add_document(self, doc_id: str, text: str, metadata: Optional[Dict[str, Any]] = None):
        """Add document to keyword index and SQLite."""
        if not text or not text.strip():
            return
        
        cursor = self.conn.cursor()
        
        # Store in SQLite
        meta_json = json.dumps(metadata) if metadata else None
        cursor.execute("""
            INSERT OR REPLACE INTO documents (id, content, metadata)
            VALUES (?, ?, ?)
        """, (doc_id, text.strip(), meta_json))
        self.conn.commit()
        
        # Update in-memory index only if BM25 is available
        if self.enabled and doc_id not in self.doc_ids:
            self.doc_ids.append(doc_id)
            self.doc_contents.append(text.strip())
            
            # Rebuild BM25 index (more efficient to update incrementally in production)
            if HAS_BM25:
                tokenized_docs = [self._tokenize(content) for content in self.doc_contents]
                self.bm25 = BM25Okapi(tokenized_docs)
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, float, str]]:
        """
        Search for documents using BM25 scoring.
        Returns: [(doc_id, bm25_score, content)]
        """
        # Return empty results if BM25 is not available
        if not self.enabled or not self.bm25 or not query:
            return []
        
        # Tokenize query
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top k documents
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include documents with positive scores
                results.append((
                    self.doc_ids[idx],
                    float(scores[idx]),
                    self.doc_contents[idx]
                ))
        
        return results
    
    def remove_document(self, doc_id: str):
        """Remove document from index and SQLite."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        self.conn.commit()
        
        # Rebuild index after deletion
        self._rebuild_index()
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row['id'],
                'content': row['content'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else None,
                'created_at': row['created_at']
            }
        return None
    
    def clear_all(self):
        """Clear all documents from the index."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM documents")
        self.conn.commit()
        
        # Clear in-memory index
        self.doc_ids = []
        self.doc_contents = []
        self.bm25 = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the keyword index."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM documents")
        count = cursor.fetchone()['count']
        
        return {
            'total_documents': count,
            'index_type': 'BM25',
            'storage': 'SQLite',
            'db_path': self.db_path
        }
    
    def close(self):
        """Close database connection."""
        self.conn.close()


# Global instance for easy access
_keyword_index = None

def get_keyword_index() -> KeywordSearchIndex:
    """Get or create the global keyword index instance."""
    global _keyword_index
    if _keyword_index is None:
        _keyword_index = KeywordSearchIndex()
    return _keyword_index