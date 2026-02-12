# core/ingestion.py
import os
from llama_parse import LlamaParse
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from domain.config import (
    PDF_PATH, VECTOR_DB_PATH, CHUNK_SIZE, CHUNK_OVERLAP, 
    EMBEDDING_MODEL, LLAMA_CLOUD_API_KEY
)

def inject_metadata(text):
    """
    Simple keyword-based metadata injection for Zone and Category.
    In a real production system, this could be an LLM call.
    """
    metadata = {
        "zone": "General", # Default
        "category": "General"
    }
    
    # Zone Heuristics
    if "Island City" in text:
        metadata["zone"] = "Island City"
    elif "Suburbs" in text or "Suburban" in text:
        metadata["zone"] = "Suburbs"
        
    # Category Heuristics
    if "Residential" in text:
        metadata["category"] = "Residential"
    elif "Commercial" in text:
        metadata["category"] = "Commercial"
    elif "Industrial" in text:
        metadata["category"] = "Industrial"
        
    return metadata

def ingest_documents():
    if not os.path.exists(PDF_PATH):
        print(f"Error: File {PDF_PATH} not found.")
        return

    print(f"Loading {PDF_PATH} using LlamaParse...")
    parser = LlamaParse(
        result_type="markdown",
        api_key=LLAMA_CLOUD_API_KEY,
        verbose=True
    )
    
    llama_documents = parser.load_data(PDF_PATH)
    print(f"Loaded {len(llama_documents)} pages via LlamaParse.")

    print("Merging pages into a single text stream...")
    full_text = "\n\n".join([doc.text for doc in llama_documents])
    
    # Note: We are creating ONE big document first, then splitting.
    # The metadata extraction ideally happens AT THE CHUNK LEVEL.
    # So we split the text first, then iterate through chunks to add metadata.
    
    print("Splitting text into context-aware chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    # Split the raw text directly
    raw_chunks = text_splitter.split_text(full_text)
    
    final_documents = []
    print("Injecting metadata into chunks...")
    for i, chunk_text in enumerate(raw_chunks):
        meta = inject_metadata(chunk_text)
        meta["source"] = PDF_PATH
        meta["chunk_id"] = i
        doc = Document(page_content=chunk_text, metadata=meta)
        final_documents.append(doc)
        
    print(f"Created {len(final_documents)} semantic chunks with metadata.")

    print(f"Creating embeddings using {EMBEDDING_MODEL}...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    
    vectorstore = FAISS.from_documents(final_documents, embeddings)
    
    print(f"Saving vector store to {VECTOR_DB_PATH}...")
    vectorstore.save_local(VECTOR_DB_PATH)
    print("Ingestion complete!")

if __name__ == "__main__":
    ingest_documents()
