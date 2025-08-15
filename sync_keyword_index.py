"""
Sync existing Pinecone documents to the keyword index.
"""

from vec_memory import export_all
from keyword_search import get_keyword_index
import json


def sync_existing_documents():
    """Export all documents from Pinecone and add to keyword index."""
    
    print("Syncing existing documents to keyword index...")
    
    # Get all documents from Pinecone
    try:
        documents = export_all()
        print(f"Found {len(documents)} documents in Pinecone")
        
        if not documents:
            print("No documents found in Pinecone. The index may be empty.")
            return
        
        # Get keyword index
        keyword_index = get_keyword_index()
        
        # Add each document to keyword index
        success_count = 0
        for doc in documents:
            try:
                doc_id = doc.get('id')
                text = doc.get('text', '')
                metadata = doc.get('metadata', {})
                
                if doc_id and text:
                    keyword_index.add_document(doc_id, text, metadata)
                    success_count += 1
                    
                    if success_count % 10 == 0:
                        print(f"Synced {success_count} documents...")
                        
            except Exception as e:
                print(f"Error syncing document {doc.get('id')}: {e}")
                continue
        
        print(f"\nSuccessfully synced {success_count} documents to keyword index")
        
        # Show stats
        stats = keyword_index.get_stats()
        print(f"Keyword index now contains {stats['total_documents']} documents")
        
    except Exception as e:
        print(f"Error during sync: {e}")


if __name__ == "__main__":
    sync_existing_documents()