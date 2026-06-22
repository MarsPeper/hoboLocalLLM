# LocalRAG: Fully Local RAG System with Qdrant & React/Vite

LocalRAG is a fully local, privacy-focused Retrieval-Augmented Generation (RAG) system. It enables you to upload documents (PDF, DOCX, TXT, MD), split them into chunks, generate vector embeddings locally, and store them in a local Qdrant database. You can then chat with your documents using a local LLM via `llama-server`. No data leaves your machine, and no API keys or internet connections are required after setup.

---

## 🚀 Features

- **Document Ingestion**: Supports drag-and-drop uploads for PDF, DOCX, TXT, and Markdown files.
- **Recursive Chunking**: Smart paragraph-boundary splitting with customizable chunk sizes and overlap values.
- **Local Embeddings**: Runs Hugging Face `sentence-transformers` (defaulting to `all-MiniLM-L6-v2`) locally on CPU or CUDA.
- **Disk-Persisted Database**: Utilizes an embedded Qdrant database stored locally on disk (`qdrant_db/`), requiring no separate database server or Docker container.
- **Sleek React Web UI**: A beautiful, premium dark-themed single-page app (SPA) built using Vite and React, featuring Server-Sent Events (SSE) streaming responses, citation links, matching scores, and real-time settings adjustments.

---

## 📁 Directory Structure

```text
LocalRAG/
├── backend/
│   ├── api.py                  # FastAPI server and endpoints
│   ├── config.yaml             # Main configuration parameters (RAG, embedding, Qdrant, LLM)
│   ├── document_processor.py   # Text extractors and Recursive Character Text Splitter
│   ├── embeddings_manager.py   # Handles SentenceTransformer embeddings and LLM API fallbacks
│   ├── vector_store.py         # Local Qdrant client wrapper (query_points, scroll, delete, reset)
│   ├── llm_connector.py        # Local LLM completion connector (supporting SSE streaming)
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
│   │       └── Settings.jsx        # Dashboard for config.yaml tweaks
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
- Install backend dependencies (`fastapi`, `qdrant-client`, `sentence-transformers`, `torch`, `pypdf`, `python-docx`, `pyyaml`, `httpx`).
- Run `npm install` inside the frontend React application.

---

## 🏃 Running the System

### Step 1: Start your Local LLM Server
In a separate terminal, launch your local GGUF model using `llama-server`. Ensure that the server runs with embedding support:
```powershell
conda activate LocalLLM
llama-server -m "C:\LLMModels\your_model.gguf" -c 8192 --host 0.0.0.0 --port 8080 --embedding
```
*(You can also use the startup script located in the root `/LocalLLM` directory if configured.)*

### Step 2: Launch LocalRAG
In your PowerShell console inside the `LocalRAG` directory, run:
```powershell
.\start_rag.ps1
```
This will:
1. Start the FastAPI backend server on `http://localhost:8000`.
2. Start the Vite React development server on `http://localhost:5173`.
3. Wait 3 seconds for both environments to boot up.
4. Launch your default browser and open the dashboard.

---

## 💡 How to Use

### 1. Indexing Documents
- Select the **Document Library** tab in the sidebar.
- Drag and drop a `.pdf`, `.docx`, `.txt`, or `.md` file into the upload zone (or click to browse).
- Watch the progress bar as the system extracts the text, splits it into overlapping segments, embeds them, and inserts them into Qdrant.
- Uploaded files will immediately appear in the **Indexed Document Library** table.

### 2. Conversational Chat
- Select the **RAG Chat** tab in the sidebar.
- Ask questions regarding your uploaded files.
- The assistant will respond, streaming tokens dynamically.
- Below the response, click the **Retrieved Sources** accordion to inspect which document chunks were pulled, their text content, and their cosine similarity matching score.

### 3. Tuning Parameters
- Select the **RAG Config** tab in the sidebar.
- Tweak the chunk size, overlap, temperature, retrieval limits, and local LLM ports.
- Edit the **System Instruction Template** to define the persona and fallback behaviors (e.g. telling the model to say "I don't know" when context is missing).
- Click **Save Configuration**. The changes will write back to `config.yaml` and hot-reload components on the backend immediately without rebooting the server.
