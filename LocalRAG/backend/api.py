import os
import yaml
import json
import shutil
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

# Import pipeline components
from document_processor import process_document
from embeddings_manager import EmbeddingsManager
from vector_store import VectorStore
from llm_connector import LLMConnector

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base Directories
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BACKEND_DIR, "config.yaml")
UPLOAD_DIR = os.path.join(BACKEND_DIR, "temp_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Local RAG System API")

# Configure CORS for React development server (port 5173 by default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local setup, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument the FastAPI app for Prometheus monitoring and expose /metrics endpoint
Instrumentator().instrument(app).expose(app)

# Global variables for components
config = {}
embeddings_manager = None
vector_store = None
llm_connector = None

def load_system_config():
    """Loads configuration from config.yaml."""
    global config
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Configuration file not found at: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config

def initialize_components():
    """Initializes/Re-initializes all pipeline components based on active configuration."""
    global config, embeddings_manager, vector_store, llm_connector
    
    load_system_config()
    
    # Extract settings
    rag_conf = config.get("rag", {})
    emb_config = config.get("embedding", {})
    qdrant_config = config.get("qdrant", {})
    llm_config = config.get("llm", {})
    
    # 1. Initialize Embeddings Manager
    embeddings_manager = EmbeddingsManager(
        model_name=emb_config.get("model_name", "all-MiniLM-L6-v2"),
        sparse_model_name=emb_config.get("sparse_model_name", "Qdrant/bm25"),
        device=emb_config.get("device", "cpu"),
        api_url=llm_config.get("api_url", "http://localhost:8080/v1")
    )
    
    # 2. Resolve Qdrant storage path
    qdrant_path = qdrant_config.get("path")
    if qdrant_path and not os.path.isabs(qdrant_path):
        qdrant_path = os.path.join(BACKEND_DIR, qdrant_path)
        
    # 3. Initialize Vector Store (using dense and sparse embeddings from manager)
    vector_store = VectorStore(
        collection_name=qdrant_config.get("collection_name", "local_rag_documents"),
        dense_embeddings=embeddings_manager.dense_embeddings,
        sparse_embeddings=embeddings_manager.sparse_embeddings,
        path=qdrant_path,
        url=qdrant_config.get("url"),
        use_hybrid_search=rag_conf.get("use_hybrid_search", True)
    )
    
    # 4. Initialize LLM Connector
    llm_connector = LLMConnector(
        api_url=llm_config.get("api_url", "http://localhost:8080/v1"),
        model_name=llm_config.get("model_name", "local-model")
    )
    logger.info("LangChain RAG pipeline components initialized successfully.")

# Initial initialization via FastAPI startup event to avoid double-locking local Qdrant during uvicorn reload
@app.on_event("startup")
def startup_event():
    initialize_components()


@app.get("/api/health")
def health_check():
    """Lightweight health check endpoint returning success without database query."""
    return {"status": "ok"}



class QueryRequest(BaseModel):
    question: str
    stream: bool = True

class ConfigUpdateRequest(BaseModel):
    rag: Dict[str, Any]
    embedding: Dict[str, Any]
    qdrant: Dict[str, Any]
    llm: Dict[str, Any]


@app.get("/api/config")
def get_config():
    """Returns the current active configuration."""
    try:
        return load_system_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config")
def update_config(updated: ConfigUpdateRequest):
    """Updates config.yaml and re-initializes pipeline components."""
    try:
        new_config = updated.model_dump()
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(new_config, f, default_flow_style=False)
        
        # Re-initialize with new parameters
        initialize_components()
        return {"status": "success", "message": "Configuration updated and pipeline re-initialized."}
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
def list_documents():
    """Lists all uniquely indexed files in the database."""
    try:
        return vector_store.get_indexed_files()
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{file_name}")
def delete_document(file_name: str):
    """Deletes all chunks of a specific document from the index."""
    try:
        vector_store.delete_file(file_name)
        return {"status": "success", "message": f"Document '{file_name}' deleted."}
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reset")
def reset_database():
    """Clears the collection entirely."""
    try:
        vector_store.reset_database()
        return {"status": "success", "message": "Database collection cleared."}
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Registry to track the real-time progress of document ingestion tasks
ingestion_statuses: Dict[str, Dict[str, Any]] = {}

def async_ingest_document(temp_path: str, filename: str, chunk_size: int, chunk_overlap: int):
    """Worker function executed in the background to chunk and embed documents in batches."""
    try:
        ingestion_statuses[filename] = {
            "status": "extracting",
            "total_chunks": 0,
            "processed_chunks": 0,
            "error": None
        }
        logger.info(f"[Background Ingest] Extracting text from {filename}...")
        documents = process_document(temp_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
        if not documents:
            ingestion_statuses[filename] = {
                "status": "failed",
                "total_chunks": 0,
                "processed_chunks": 0,
                "error": "Document yielded no text content."
            }
            logger.error(f"[Background Ingest] Extraction failed for {filename}: No text content.")
            return

        total_chunks = len(documents)
        ingestion_statuses[filename] = {
            "status": "indexing",
            "total_chunks": total_chunks,
            "processed_chunks": 0,
            "error": None
        }
        logger.info(f"[Background Ingest] Indexing {total_chunks} chunks for {filename} to Qdrant...")

        # Batch insert chunks (e.g. 5 at a time) to report progress in real-time
        batch_size = 5
        for i in range(0, total_chunks, batch_size):
            batch = documents[i:i + batch_size]
            vector_store.add_documents(batch)
            processed = min(i + batch_size, total_chunks)
            ingestion_statuses[filename]["processed_chunks"] = processed
            logger.info(f"[Background Ingest] Embedded {processed}/{total_chunks} chunks for {filename}")

        ingestion_statuses[filename]["status"] = "completed"
        logger.info(f"[Background Ingest] Ingestion completed for {filename}!")
        
    except Exception as e:
        logger.error(f"[Background Ingest] Failed to ingest {filename}: {e}")
        ingestion_statuses[filename] = {
            "status": "failed",
            "total_chunks": 0,
            "processed_chunks": 0,
            "error": str(e)
        }
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as clean_ex:
                logger.error(f"[Background Ingest] Failed to clean temp upload: {clean_ex}")

@app.post("/api/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Uploads a file, writes it to temp directory, and initiates background indexing."""
    temp_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        # Save upload to temporary file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"Queued file for background processing: {file.filename}")
        
        # Load parameters from config
        rag_conf = config.get("rag", {})
        chunk_size = rag_conf.get("chunk_size", 500)
        chunk_overlap = rag_conf.get("chunk_overlap", 50)
        
        # Queue the background processing task
        background_tasks.add_task(
            async_ingest_document,
            temp_path,
            file.filename,
            chunk_size,
            chunk_overlap
        )
        
        return {
            "status": "queued",
            "file_name": file.filename
        }
    except Exception as e:
        logger.error(f"Failed to queue upload {file.filename}: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/upload/status/{file_name}")
def get_upload_status(file_name: str):
    """Polls real-time progress of document ingestion."""
    if file_name in ingestion_statuses:
        return ingestion_statuses[file_name]
        
    # Fallback check: if completed in a previous run and already saved in vector store
    try:
        indexed_files = vector_store.get_indexed_files()
        for f in indexed_files:
            if f.get("file_name") == file_name:
                return {
                    "status": "completed",
                    "total_chunks": f.get("chunk_count", 0),
                    "processed_chunks": f.get("chunk_count", 0),
                    "error": None
                }
    except Exception as e:
        logger.error(f"Error querying indexed files list: {e}")
        
    raise HTTPException(status_code=404, detail="Ingestion job status not found for this file.")

@app.post("/api/query")
def query_pipeline(request: QueryRequest):
    """Processes user query: search similarity -> prompt construct -> LLM generate."""
    try:
        # Step 1: Search similarity (uses hybrid search & FlashRank reranking if enabled)
        rag_conf = config.get("rag", {})
        top_k = rag_conf.get("top_k", 4)
        use_reranker = rag_conf.get("use_reranker", True)
        reranker_model = rag_conf.get("reranker_model", "ms-marco-MiniLM-L-12-v2")
        base_retrieve_k = rag_conf.get("base_retrieve_k", 12)
        
        sources = vector_store.search_similar(
            query=request.question,
            top_k=top_k,
            use_reranker=use_reranker,
            reranker_model=reranker_model,
            base_retrieve_k=base_retrieve_k
        )
        
        # Step 2: Construct LLM prompt
        context_blocks = []
        for src in sources:
            context_blocks.append(
                f"Source: {src['file_name']} (Chunk {src['chunk_index']}):\n{src['content']}"
            )
            
        if context_blocks:
            context_str = "\n\n".join(context_blocks)
        else:
            context_str = "No relevant context found. Answer with 'I do not have enough information to answer this question.'"
            
        llm_conf = config.get("llm", {})
        system_prompt_template = llm_conf.get("system_prompt", "")
        formatted_system_prompt = system_prompt_template.replace("{context}", context_str).replace("{question}", request.question)
        
        temperature = llm_conf.get("temperature", 0.1)
        max_tokens = llm_conf.get("max_tokens", 1024)
        
        # Helper generator for SSE streaming response
        def response_generator():
            try:
                # First yield the sources/citations JSON
                yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
                
                # Next stream LLM tokens
                if request.stream:
                    for token in llm_connector.generate_response_stream(
                        system_prompt=formatted_system_prompt,
                        user_question=request.question,
                        temperature=temperature,
                        max_tokens=max_tokens
                    ):
                        yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
                else:
                    response_text = llm_connector.generate_response(
                        system_prompt=formatted_system_prompt,
                        user_question=request.question,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    yield f"data: {json.dumps({'type': 'token', 'token': response_text})}\n\n"
                    
                yield "data: [DONE]\n\n"
            except Exception as inner_err:
                logger.error(f"Stream generation error: {inner_err}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(inner_err)})}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(response_generator(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error querying RAG pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
