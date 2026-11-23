import os
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv()

from langchain_text_splitters import RecursiveCharacterTextSplitter
from services.rag_engine import chroma_client, embeddings_model, ingest_document

# Import all 10 documents
from knowledge_data.doc1_doc2_ml_trees import DOCUMENTS as ml_trees_docs
from knowledge_data.doc3_doc4_ml_regression import DOCUMENTS as ml_reg_docs
from knowledge_data.doc5_doc6_networks import DOCUMENTS as net_docs
from knowledge_data.doc7_doc8_dbms import DOCUMENTS as dbms_docs
from knowledge_data.doc9_doc10_dsa import DOCUMENTS as dsa_docs

ALL_DOCUMENTS = ml_trees_docs + ml_reg_docs + net_docs + dbms_docs + dsa_docs

def main():
    print("=" * 70, flush=True)
    print("INITIALIZING CLEAN CHROMADB KNOWLEDGE BASE FOR 4 SUBJECTS", flush=True)
    print("=" * 70, flush=True)

    # Recreate collection cleanly with high sync threshold
    try:
        chroma_client.delete_collection("course_knowledge_base")
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name="course_knowledge_base",
        metadata={"hnsw:space": "cosine", "hnsw:sync_threshold": 100000, "hnsw:batch_size": 10000}
    )
    print(f"Clean 'course_knowledge_base' collection created.", flush=True)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=550,
        chunk_overlap=60,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    all_chunks = []
    all_metadatas = []
    all_ids = []

    for doc in ALL_DOCUMENTS:
        doc_name = doc["document"]
        topic = doc["topic"]
        section = doc["section"]
        pages = doc["pages"]

        print(f"Parsing {doc_name} ({topic} | {section}) - {len(pages)} pages", flush=True)

        for page in pages:
            page_num = page["page"]
            text = page["text"].strip()
            if not text:
                continue

            chunks = text_splitter.split_text(text)
            for c_idx, chunk_text in enumerate(chunks):
                chunk_id = f"{doc_name}_p{page_num}_c{c_idx}"
                all_chunks.append(chunk_text)
                all_metadatas.append({
                    "document": doc_name,
                    "page": page_num,
                    "topic": topic,
                    "section": section
                })
                all_ids.append(chunk_id)

    total_chunks = len(all_chunks)
    print(f"\nGenerated {total_chunks} structured chunks across all 10 documents.", flush=True)

    batch_size = 15
    total_batches = (total_chunks + batch_size - 1) // batch_size
    print(f"Embedding and upserting in {total_batches} batches...", flush=True)

    for b in range(total_batches):
        start = b * batch_size
        end = min(start + batch_size, total_chunks)
        b_chunks = all_chunks[start:end]
        b_metas = all_metadatas[start:end]
        b_ids = all_ids[start:end]

        print(f"  -> Batch {b+1}/{total_batches} ({len(b_chunks)} chunks)...", flush=True)

        embs = None
        for attempt in range(5):
            try:
                embs = embeddings_model.embed_documents(b_chunks)
                break
            except Exception as e:
                wait_sec = 35.0 if ("RESOURCE_EXHAUSTED" in str(e) or "429" in str(e)) else 3.0
                print(f"     [Wait] API quota pause on batch {b+1}: waiting {wait_sec}s...", flush=True)
                time.sleep(wait_sec)

        if embs is None:
            raise RuntimeError(f"Failed to embed batch {b+1}")

        collection.upsert(
            ids=b_ids,
            documents=b_chunks,
            metadatas=b_metas,
            embeddings=embs
        )
        time.sleep(1.0)

    # Ingest sample_boosting.pdf if present
    if os.path.exists("sample_boosting.pdf"):
        print("\nAlso indexing existing sample_boosting.pdf...", flush=True)
        try:
            ingest_document("sample_boosting.pdf", topic="Machine Learning", section="Ensemble Methods")
        except Exception as e:
            print(f"Note on sample_boosting.pdf: {e}", flush=True)

    total_count = collection.count()
    print("\n" + "=" * 70, flush=True)
    print(f"INGESTION COMPLETE! Total chunks in ChromaDB: {total_count}", flush=True)
    print("=" * 70, flush=True)

    # Verify query for each of the 4 subjects
    print("\nVERIFYING SEARCH ACROSS ALL 4 SUBJECTS:\n", flush=True)
    test_queries = [
        ("Machine Learning", "How does Random Forest reduce decision tree variance?"),
        ("Machine Learning", "What is the normal equation formula for Linear Regression?"),
        ("Computer Networks", "What are the 7 layers of the OSI model and data encapsulation?"),
        ("Computer Networks", "Explain the TCP 3-way handshake SYN SYN-ACK ACK process."),
        ("Database Management Systems", "How does 2NF eliminate partial dependency and 3NF eliminate transitive dependency?"),
        ("Database Management Systems", "What are the ACID properties in database transactions?"),
        ("Data Structures & Algorithms", "How does binary search achieve O(log n) time complexity?"),
        ("Data Structures & Algorithms", "What is the loop invariant for the Quicksort partition algorithm?")
    ]

    for topic, q in test_queries:
        q_vec = embeddings_model.embed_query(q)
        res = collection.query(query_embeddings=[q_vec], n_results=1)
        if res and res["documents"] and res["documents"][0]:
            top_doc = res["metadatas"][0][0]
            snippet = res["documents"][0][0][:130].replace("\n", " ")
            print(f"[{topic}] Query: '{q}'", flush=True)
            print(f"  -> Found in: {top_doc.get('document')} (Page {top_doc.get('page')})", flush=True)
            print(f"  -> Snippet: \"{snippet}...\"\n", flush=True)

if __name__ == "__main__":
    main()
