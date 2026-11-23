import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# --- MONKEYPATCH: Bypass ChromaDB's forced ONNX/onnxruntime dependency ---
class MockONNX:
    def __init__(self, *args, **kwargs):
        pass
    def __call__(self, *args, **kwargs):
        return []

import chromadb.utils.embedding_functions as ef
ef.ONNXMiniLM_L6_V2 = MockONNX
# -----------------------------------------------------------------------

import chromadb
from chromadb.config import Settings
from chromadb.api.types import Documents, Embeddings, EmbeddingFunction
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")

CHROMA_DATA_PATH = os.path.join(os.path.dirname(__file__), "../chroma_db")

# Dummy embedding function export for custom ChromaDB collections (e.g., qa_cache)
class DummyEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        return [[0.0] * 768 for _ in input]

# Initialize persistent ChromaDB client with telemetry disabled
chroma_client = chromadb.PersistentClient(
    path=CHROMA_DATA_PATH,
    settings=Settings(anonymized_telemetry=False)
)

# Use Google's API for actual embeddings if available
try:
    if GEMINI_API_KEY:
        embeddings_model = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-2-preview", 
            google_api_key=GEMINI_API_KEY
        )
    else:
        embeddings_model = None
except Exception as e:
    print(f"[RAG Engine] Notice: Could not initialize Google embeddings ({e}).")
    embeddings_model = None

collection = chroma_client.get_or_create_collection(
    name="course_knowledge_base",
    metadata={"hnsw:space": "cosine", "hnsw:sync_threshold": 100000, "hnsw:batch_size": 10000}
)

def ingest_document(pdf_path: str, topic: str, section: str = "General") -> int:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
    
    doc_name = os.path.basename(pdf_path)
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = text_splitter.split_documents(pages)
    
    documents, metadatas, ids = [], [], []
    for idx, doc in enumerate(docs):
        documents.append(doc.page_content)
        metadatas.append({
            "document": doc_name, 
            "page": doc.metadata.get("page", 0) + 1, 
            "topic": topic, 
            "section": section
        })
        ids.append(f"{doc_name}_chunk_{idx}")

    if documents:
        print(f"[RAG Engine] Computing embeddings for {len(documents)} chunks via Google API...", flush=True)
        computed_embeddings = embeddings_model.embed_documents(documents)
        
        print(f"[RAG Engine] Upserting chunks into ChromaDB...", flush=True)
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=computed_embeddings
        )
    
    print(f"[RAG Engine] Ingestion complete! Total chunks stored: {len(documents)}", flush=True)
    return len(documents)

def query_knowledge_base(query_text: str, n_results: int = 3) -> list[dict]:
    if not embeddings_model:
        return []
    try:
        print("   [DEBUG] Embedding query text via Google API...", flush=True)
        query_vector = embeddings_model.embed_query(query_text)
        
        print("   [DEBUG] Querying ChromaDB collection...", flush=True)
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=n_results
        )
        
        retrieved_items = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            for doc, meta in zip(docs, metas):
                retrieved_items.append({
                    "document": meta.get("document"),
                    "page": meta.get("page"),
                    "topic": meta.get("topic"),
                    "section": meta.get("section"),
                    "text": doc
                })
                
        print(f"   [DEBUG] Retrieved {len(retrieved_items)} chunks from ChromaDB.", flush=True)
        return retrieved_items
    except Exception as e:
        print(f"   [DEBUG] ChromaDB query notice ({e}). Proceeding with expert model knowledge.", flush=True)
        return []