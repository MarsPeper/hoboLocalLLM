# LocalRAG: Fully Local RAG System with Qdrant, LangChain & React/Vite

LocalRAG is a fully local, privacy-focused Retrieval-Augmented Generation (RAG) system. It enables you to upload documents (PDF, DOCX, TXT, MD), split them into chunks, generate vector embeddings locally, and store them in a local Qdrant database. You can then chat with your documents using a local LLM via `llama-server`. No data leaves your machine, and no API keys or internet connections are required after setup.

This version has been migrated to **LangChain** and enhanced with industry-standard features, including **Hybrid Search (Dense + Sparse/BM25)**, **Contextual Compression & Reranking (FlashRank)**, and a **Model Evaluation Benchmark Suite**.

---

## 🚀 Features

- **LangChain Integration**: Built on LangChain's unified architecture for document processing, vector search, and LLM orchestration.
- **Document Ingestion**: Supports drag-and-drop uploads for PDF, DOCX, TXT, and Markdown files.
- **Recursive Chunking**: Smart paragraph-boundary splitting using LangChain's `RecursiveCharacterTextSplitter`.
- **Hybrid Search**: Combines **Dense Vectors** (for semantic/contextual understanding) and **Sparse Vectors** (using FastEmbed's SPLADE/BM25 for exact keyword matches) to retrieve highly relevant context.
- **FlashRank Reranking**: Uses a CPU-friendly local Cross-Encoder model (`ms-marco-MiniLM-L-12-v2`) to re-order and filter the top candidates before sending them to the LLM.
- **Sleek React Web UI**: A beautiful, premium dark-themed single-page app (SPA) built using Vite and React, featuring Server-Sent Events (SSE) streaming responses, citation links, matching scores, and real-time settings adjustments (with sliders for hybrid and rerank options).
- **Model Benchmark Suite**: An offline evaluation script (`benchmark_models.py`) to test different models and measure Time to First Token (TTFT), tokens per second (TPS), factual correctness, and refusal accuracy.

---

## 📁 Directory Structure

```text
LocalRAG/
├── backend/
│   ├── api.py                  # FastAPI server and endpoints
│   ├── config.yaml             # Main configuration parameters (RAG, embedding, Qdrant, LLM)
│   ├── document_processor.py   # LangChain Text loaders and Recursive Text Splitter
│   ├── embeddings_manager.py   # Handles Hugging Face Dense Embeddings and FastEmbed Sparse Embeddings
│   ├── vector_store.py         # LangChain QdrantVectorStore wrapper and FlashRank reranking
│   ├── llm_connector.py        # LangChain ChatOpenAI local completion connector
│   ├── benchmark_models.py     # Evaluation script to test LLM model performance (TTFT, TPS, accuracy)
│   ├── requirements.txt        # Backend Python requirements
│   └── test_rag.py             # Validation script to test the backend pipeline
├── frontend/                   # React + Vite application
│   ├── index.html              # Main HTML container with Google Fonts
│   ├── package.json            # React development dependencies
│   ├── src/
│   │   ├── App.jsx             # App layout and navigation
│   │   ├── index.css           # Premium stylesheet (glassmorphism design)
│   │   └── components/
│   │       ├── Chat.jsx            # SSE Chat component with citation accordions
│   │       ├── DocumentManager.jsx # Upload area and document registry
│   │       └── Settings.jsx        # Dashboard for config.yaml tweaks (hybrid and rerank toggles)
├── install.ps1                 # Automatic setup script for Python + Node
└── start_rag.ps1               # Launcher script for FastAPI + Vite
```

---

## 🛠️ Installation & Setup

### Prerequisites
Make sure you have the following installed on your Windows machine:
1. **Node.js** (v18 or higher) - [Download Node.js](https://nodejs.org/)
2. **Anaconda** or **Miniconda** - [Download Miniconda](https://docs.anaconda.com/miniconda/)
3. Ensure `conda`, `node`, and `npm` are registered in your system PATH environment.

### 1. Run the Installer
Open PowerShell, navigate to the `LocalRAG` directory, and execute the installer script:
```powershell
cd C:\Projects\hoboLocalLLM\LocalRAG
.\install.ps1
```
This script will:
- Verify your Node and Conda installations.
- Verify or create the `LocalLLM` conda environment.
- Install python=3.11 and pip inside the `LocalLLM` environment for clean isolation.
- Install backend dependencies (`fastapi`, `qdrant-client`, `langchain`, `fastembed`, `flashrank`, etc.).
- Run `npm install` inside the frontend React application.

---

## 🏃 Running the System

### Step 1: Start your Local LLM Server
Ensure you have downloaded a GGUF model. We recommend Microsoft's **[Phi-4 Mini Instruct (Q8_0)](https://huggingface.co/unsloth/Phi-4-mini-instruct-GGUF/resolve/main/Phi-4-mini-instruct.Q8_0.gguf?download=true)**.

In a separate terminal, launch your local GGUF model using `llama-server`. Ensure that the server runs with embedding support:
```powershell
conda activate LocalLLM
llama-server -m "C:\LLMModels\Phi-4-mini-instruct.Q8_0.gguf" -c 8192 --host 0.0.0.0 --port 8080 --embedding
```
*(You can also use the startup script located in the root `/LocalLLM` directory if configured.)*

### Step 2: Launch LocalRAG
In your PowerShell console inside the `LocalRAG` directory, run:
```powershell
.\start_rag.ps1
```
This will start the FastAPI backend, launch the Vite React dev server, and open your browser to `http://localhost:5173`.

---

## 📊 Model Evaluation Benchmark Suite

To compare different GGUF models on your machine and determine if they are fast and accurate enough for RAG, run the benchmark suite:

```powershell
conda activate LocalLLM
cd backend
python benchmark_models.py
```

This script will:
1. Ingest a set of test documents into a temporary Qdrant benchmark index.
2. Run standard RAG queries (factual, technical, and off-context questions).
3. Measure and report:
   - **Time to First Token (TTFT)** (indicates generation latency).
   - **Generation Throughput (TPS)** (tokens generated per second).
   - **Quality Check**: Whether the model included expected keywords (factual correctness) and successfully refused to answer off-context questions (hallucination check).
4. Output a summary report comparing active parameters and performance grades.

---

## 💡 How to Use

### 1. Indexing Documents
- Select the **Document Library** tab in the sidebar.
- Drag and drop a `.pdf`, `.docx`, `.txt`, or `.md` file into the upload zone.
- The system will extract text, split it into chunks, generate both dense and sparse vectors, and index them.

### 2. Conversational Chat
- Select the **RAG Chat** tab.
- Ask questions regarding your uploaded files.
- The assistant will stream responses. Click **Retrieved Sources** below to view chunk text and matches.

### 3. Tuning Parameters
- Select the **RAG Config** tab.
- You can toggle **Hybrid Search** and **Reranking** on/off, modify chunk size, limits, temperature, or rewrite the system prompt template.
- Click **Save Configuration** to immediately apply the settings without restarting the server.
