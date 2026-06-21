import os
import uuid
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import config

_embedding_model = None
_qdrant_client = None

def get_embedding_model():
    """Returns a singleton instance of the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        import os
        os.environ["CURL_CA_BUNDLE"] = ""
        os.environ["REQUESTS_CA_BUNDLE"] = ""
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
        _embedding_model = SentenceTransformer(
            config.EMBEDDING_MODEL
        )
    return _embedding_model

def get_qdrant_client():
    """Singleton getter for the Qdrant Client, with fallback to in-memory mode."""
    global _qdrant_client
    if _qdrant_client is not None:
        return _qdrant_client
        
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if qdrant_url:
        try:
            url = qdrant_url.strip()
            api_key = qdrant_api_key.strip() if qdrant_api_key else None
            
            client = QdrantClient(url=url, api_key=api_key, timeout=10)
            client.get_collections()  # connection verification
            _qdrant_client = client
            return _qdrant_client
        except Exception as e:
            print(f"Warning: Failed to connect to Qdrant Cloud: {e}. Falling back to in-memory Qdrant.")
            
    # In-memory database fallback
    _qdrant_client = QdrantClient(":memory:")
    return _qdrant_client

def reset_qdrant_client():
    """Resets the Qdrant client singleton so it will be re-initialized on next call."""
    global _qdrant_client
    _qdrant_client = None

def ingest_pdf(file_path: str, client=None, collection_name: str = None) -> int:
    """Extract, chunk, embed, and upload PDF content to Qdrant."""
    if client is None:
        client = get_qdrant_client()
    if collection_name is None:
        collection_name = config.COLLECTION_NAME
        
    # Ensure collection exists
    try:
        client.get_collection(collection_name)
    except Exception:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        
    # Read PDF text page by page
    text_by_page = []
    with pdfplumber.open(file_path) as pdf:
        for idx, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text_by_page.append((idx + 1, page_text))
                
    if not text_by_page:
        raise ValueError("This PDF appears to be scanned. OCR support coming soon.")
        
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP
    )
    
    model = get_embedding_model()
    points = []
    chunk_count = 0
    
    for page_num, text in text_by_page:
        chunks = splitter.split_text(text)
        for chunk_idx, chunk in enumerate(chunks):
            # Compute embeddings
            vector = model.encode(chunk).tolist()
            point_id = str(uuid.uuid4())
            payload = {
                "text": chunk,
                "source_file": os.path.basename(file_path),
                "page_number": page_num,
                "chunk_index": chunk_idx
            }
            points.append(PointStruct(id=point_id, vector=vector, payload=payload))
            chunk_count += 1
            
    # Upsert points in batches (if large, but Qdrant upsert is fast for small-med PDFs)
    if points:
        client.upsert(
            collection_name=collection_name,
            wait=True,
            points=points
        )
        
    return chunk_count

def clear_db(client=None, collection_name: str = None):
    """Deletes the document collection from Qdrant."""
    if client is None:
        client = get_qdrant_client()
    if collection_name is None:
        collection_name = config.COLLECTION_NAME
        
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

