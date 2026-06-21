from pipeline.ingestion import get_qdrant_client, get_embedding_model
import config

def retrieve(query: str, client=None, collection_name: str = None, top_k: int = None) -> list[dict]:
    """Retrieve top matching documents/chunks from Qdrant for a given query."""
    if top_k is None:
        top_k = config.TOP_K_RESULTS
        
    if client is None:
        client = get_qdrant_client()
    if collection_name is None:
        collection_name = config.COLLECTION_NAME
        
    model = get_embedding_model()
    
    # Check if the collection exists; if not, return empty list
    try:
        client.get_collection(collection_name)
    except Exception:
        return []
        
    # Generate search query embedding
    query_vector = model.encode(query).tolist()
    
    # Run similarity search
    search_result = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k
    )
    
    results = []
    for hit in search_result:
        results.append({
            "text": hit.payload.get("text", ""),
            "score": hit.score,
            "metadata": {
                "source_file": hit.payload.get("source_file", ""),
                "page_number": hit.payload.get("page_number", 0),
                "chunk_index": hit.payload.get("chunk_index", 0)
            }
        })
        
    return results
