"""
Asynchronous memory operations for better performance.
"""
import asyncio
import aiohttp
from typing import List, Tuple, Dict, Any, Optional
import uuid
from concurrent.futures import ThreadPoolExecutor
import json
import time

class AsyncMemoryBackend:
    """Asynchronous memory operations for better performance."""
    
    def __init__(self, api_key: str, index_name: str):
        self.api_key = api_key
        self.index_name = index_name
        self.embed_url = "https://api.openai.com/v1/embeddings"
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.session = None
        self.embed_model = "text-embedding-3-small"
        self.embed_dim = 1536
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Asynchronously embed multiple texts."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Batch texts for efficiency (OpenAI has a limit)
        batch_size = 20
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            payload = {
                "input": batch,
                "model": self.embed_model
            }
            
            try:
                async with self.session.post(
                    self.embed_url, 
                    json=payload, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        embeddings = [item["embedding"] for item in data["data"]]
                        all_embeddings.extend(embeddings)
                    else:
                        error_text = await response.text()
                        raise Exception(f"Embedding API error {response.status}: {error_text}")
            except asyncio.TimeoutError:
                raise Exception("Embedding request timed out")
            except Exception as e:
                raise Exception(f"Embedding failed: {str(e)}")
            
            # Small delay between batches to avoid rate limiting
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)
        
        return all_embeddings
    
    async def upsert_batch(self, items: List[Tuple[str, Dict]]) -> List[str]:
        """Asynchronously upsert multiple items."""
        if not items:
            return []
        
        # Generate IDs
        ids = [str(uuid.uuid4()) for _ in items]
        
        # Extract texts
        texts = [item[0] for item in items]
        
        # Embed all texts asynchronously
        embeddings = await self.embed_batch(texts)
        
        # Prepare vectors for Pinecone
        vectors = []
        for id_, embedding, (text, metadata) in zip(ids, embeddings, items):
            vectors.append({
                "id": id_,
                "values": embedding,
                "metadata": {"text": text, **metadata}
            })
        
        # Upsert to Pinecone (run in executor as Pinecone SDK isn't async)
        await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self._sync_upsert,
            vectors
        )
        
        return ids
    
    def _sync_upsert(self, vectors):
        """Synchronous upsert for executor."""
        from vec_memory import index
        if index:
            # Batch upsert with retry logic
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i+batch_size]
                retries = 3
                for attempt in range(retries):
                    try:
                        index.upsert(vectors=batch)
                        break
                    except Exception as e:
                        if attempt == retries - 1:
                            raise
                        time.sleep(2 ** attempt)
    
    async def search_concurrent(
        self, 
        queries: List[str], 
        k: int = 5
    ) -> Dict[str, List[Tuple]]:
        """Search multiple queries concurrently."""
        if not queries:
            return {}
        
        # Embed all queries
        embeddings = await self.embed_batch(queries)
        
        # Search concurrently
        tasks = []
        for query, embedding in zip(queries, embeddings):
            task = asyncio.create_task(
                self._search_single(embedding, k)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results and exceptions
        output = {}
        for query, result in zip(queries, results):
            if isinstance(result, Exception):
                print(f"Search failed for '{query}': {result}")
                output[query] = []
            else:
                output[query] = result
        
        return output
    
    async def _search_single(
        self, 
        embedding: List[float], 
        k: int
    ) -> List[Tuple]:
        """Single async search."""
        # Run in executor as Pinecone SDK isn't async
        result = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self._sync_search,
            embedding,
            k
        )
        return result
    
    def _sync_search(self, embedding, k):
        """Synchronous search for executor."""
        from vec_memory import index
        if not index:
            return []
        
        try:
            res = index.query(vector=embedding, top_k=k, include_metadata=True)
            return [(m.id, m.metadata.get("text", ""), m.metadata) 
                    for m in res.matches]
        except Exception as e:
            print(f"Search error: {e}")
            return []

# Async PDF processor for faster ingestion
class AsyncPDFProcessor:
    """Asynchronous PDF processing for faster ingestion."""
    
    def __init__(self, memory_backend: AsyncMemoryBackend):
        self.memory = memory_backend
        self.chunk_size = 1200
        self.overlap = 200
    
    async def process_pdf(
        self, 
        file_content: bytes,
        filename: str,
        chunk_size: Optional[int] = None
    ) -> int:
        """Process PDF content asynchronously."""
        from pypdf import PdfReader
        import io
        
        # Use provided chunk size or default
        chunk_size = chunk_size or self.chunk_size
        
        # Parse PDF
        try:
            reader = PdfReader(io.BytesIO(file_content))
        except Exception as e:
            raise ValueError(f"Failed to read PDF: {str(e)}")
        
        if not reader.pages:
            raise ValueError("PDF has no pages")
        
        # Process pages concurrently
        tasks = []
        for page_num, page in enumerate(reader.pages):
            task = asyncio.create_task(
                self._process_page(page, page_num, chunk_size, filename)
            )
            tasks.append(task)
        
        # Wait for all pages with timeout
        try:
            chunks_per_page = await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=300  # 5 minute timeout for large PDFs
            )
        except asyncio.TimeoutError:
            raise Exception("PDF processing timed out")
        
        # Flatten chunks
        all_chunks = []
        for chunks in chunks_per_page:
            if chunks:
                all_chunks.extend(chunks)
        
        # Batch upsert
        if all_chunks:
            await self.memory.upsert_batch(all_chunks)
        
        return len(all_chunks)
    
    async def _process_page(
        self, 
        page, 
        page_num: int, 
        chunk_size: int,
        source: str
    ) -> List[Tuple[str, Dict]]:
        """Process single page asynchronously."""
        # Extract text (CPU-bound, use executor)
        loop = asyncio.get_event_loop()
        
        try:
            text = await loop.run_in_executor(None, page.extract_text)
        except Exception as e:
            print(f"Failed to extract text from page {page_num}: {e}")
            return []
        
        if not text or len(text.strip()) < 10:
            return []
        
        # Chunk text
        from improved_chunking import smart_chunks
        chunks = smart_chunks(text, chunk_size=chunk_size, overlap=self.overlap)
        
        # Prepare items with metadata
        items = []
        for i, chunk in enumerate(chunks):
            if chunk and len(chunk.strip()) > 10:
                metadata = {
                    "source": source,
                    "page": page_num + 1,
                    "chunk": i,
                    "type": "pdf",
                    "timestamp": time.time()
                }
                items.append((chunk, metadata))
        
        return items
    
    async def process_multiple_pdfs(
        self, 
        files: List[Tuple[bytes, str]]
    ) -> Dict[str, int]:
        """Process multiple PDFs concurrently."""
        tasks = []
        filenames = []
        
        for file_content, filename in files:
            task = asyncio.create_task(
                self.process_pdf(file_content, filename)
            )
            tasks.append(task)
            filenames.append(filename)
        
        # Process with timeout
        try:
            counts = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=600  # 10 minute timeout for batch
            )
        except asyncio.TimeoutError:
            return {fn: 0 for fn in filenames}
        
        # Build results
        results = {}
        for filename, count in zip(filenames, counts):
            if isinstance(count, Exception):
                print(f"Failed to process {filename}: {count}")
                results[filename] = 0
            else:
                results[filename] = count
        
        return results

# Helper function to run async operations from sync code
def run_async(coro):
    """Run async coroutine from synchronous code."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running (e.g., in Jupyter), create task
            task = asyncio.create_task(coro)
            return task
        else:
            # Run the coroutine
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
