import os
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()

# Embedding and Chunking Configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "compliance_docs"
TOP_K_RESULTS = 5

# LLM Configuration
LLM_MODEL = "gemini/gemini-2.5-flash"  # Default Gemini model (more reliable on free tier)

