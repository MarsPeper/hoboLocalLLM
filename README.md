# hoboLocalLLM

A fully local AI chatbot pipeline with a fully local RAG (Retrieval-Augmented Generation) system.

No cloud services. No API subscriptions. No data leaves your machine.

The only recurring cost is electricity.

## Features

- 100% local inference using `llama.cpp`
- 100% local document indexing and retrieval
- No OpenAI, Anthropic, Google, or other API dependencies
- OpenAI-compatible local endpoint
- Simple document upload workflow
- Works offline after initial setup
- Supports custom GGUF models
- Designed for small businesses, homelabs, and privacy-focused users

---

## Architecture

```text
User
 │
 ▼
Chat UI
 │
 ▼
RAG Pipeline
 │
 ├── Retrieve Relevant Chunks
 │
 ▼
Vector Database
 │
 └── Embedded Documents
 │
 ▼
llama.cpp
 │
 ▼
Local LLM (GGUF)
 │
 ▼
Response
```

### Planned Workflow

1. User uploads documents.
2. Documents are chunked automatically.
3. Chunks are converted into embeddings.
4. Embeddings are stored locally.
5. User asks a question.
6. Relevant chunks are retrieved.
7. Retrieved context is sent to the local LLM.
8. The model generates a response.

No internet connection is required after setup.

---

# Installing `llama.cpp` with Conda

This project uses `llama.cpp` as the inference engine.

Using a dedicated Conda environment helps isolate dependencies and keeps your local LLM setup organized.

## Prerequisites

Install one of the following:

- Anaconda
- Miniconda (recommended)

Verify Conda is installed:

```bash
conda --version
```

Example output:

```text
conda 25.x.x
```

---

## Step 1: Create a Dedicated Environment

Create a new environment:

```bash
conda create -n LocalLLM python=3.11 -y
```

Activate it:

```bash
conda activate LocalLLM
```

Verify the environment:

```bash
conda info --envs
```

The active environment will be marked with `*`.

---

## Step 2: Add the Conda-Forge Repository

`llama.cpp` is distributed through Conda-Forge.

Add the repository:

```bash
conda config --add channels conda-forge
```

Enable strict channel priority:

```bash
conda config --set channel_priority strict
```

This helps prevent dependency conflicts.

---

## Step 3: Install `llama.cpp`

Install the package:

```bash
conda install llama.cpp
```

Conda will automatically install all required dependencies.

---

## Step 4: Verify Installation

Verify the installation completed successfully:

```bash
llama-server --help
```

or

```bash
llama-cli --help
```

You should see a list of available command-line options.

You can also verify the package directly:

```bash
conda list llama.cpp
```

---

## Included Utilities

Depending on the installed version, the Conda package may include:

| Tool | Purpose |
|--------|---------|
| `llama-server` | OpenAI-compatible API server |
| `llama-cli` | Command-line inference |
| `llama-quantize` | Model quantization |
| `llama-bench` | Performance benchmarking |
| `llama-perplexity` | Perplexity testing |
| `llama-batched` | Batch inference examples |

---

## Step 5: Download a Model

Download a GGUF model from a model repository.

Recommended starter models:

- Phi-4 Mini Instruct
- Qwen 3
- Gemma 3
- Llama 3.2

Create a model directory:

### Windows

```text
C:\LLMModels\
```

### Linux/macOS

```text
~/LLMModels/
```

Place your downloaded `.gguf` files in this directory.

---

## Step 6: Launch the Local API Server

Example:

```bash
llama-server \
  -m "/path/to/model.gguf" \
  -c 8192 \
  --host 0.0.0.0 \
  --port 8080
```

### Command Parameters

| Parameter | Description |
|------------|------------|
| `-m` | Path to the GGUF model |
| `-c` | Context window size |
| `--host` | Network interface to bind to |
| `--port` | API server port |

After startup, the API will be available locally:

```text
http://localhost:8080
```
There's a web UI that's similar to chatgpt at http://localhost:8080/

The endpoint is compatible with:

- C#
- Python
- JavaScript
- LangChain
- LlamaIndex
- Open WebUI
- Custom RAG applications

---

## Included Startup Scripts

The `LocalLLM` folder contains startup scripts for launching a local model quickly.

### PowerShell Script

The provided PowerShell script:

- Activates the `LocalLLM` Conda environment
- Starts `llama-server`
- Uses sensible default settings
- Can be customized for your hardware

Before running the script:

1. Download a GGUF model.
2. Update the model path in the script.
3. Save the file.
4. Run the script.

Example:

```powershell
.\Start-LocalLLM.ps1
```

---

## Project Roadmap

### Phase 1 - Local Inference
- [x] llama.cpp setup
- [x] Local API endpoint

### Phase 2 - Local RAG
- [ ] Automatic document ingestion
- [ ] Chunking pipeline
- [ ] Local embedding generation
- [ ] Vector storage
- [ ] Semantic search

### Phase 3 - User Experience
- [ ] Web UI
- [ ] Drag-and-drop document uploads
- [ ] Chat history
- [ ] Source citations
- [ ] A test bench mark from synthetic data for the RAG pipeline
- [ ] A test bench mark from synthetic data for the model

### Phase 4 - Production
- [ ] Multi-user support
- [ ] Authentication
- [ ] Docker deployment
- [ ] Monitoring

---

## Troubleshooting

### Conda Command Not Found

Ensure Conda is installed and available in your system PATH.

### Package Not Found

Update Conda:

```bash
conda update -n base -c defaults conda
```

Then retry the installation.

### Wrong Environment Active

Verify:

```bash
conda activate LocalLLM
```

### GPU Not Being Used

Check:

- NVIDIA drivers are installed
- CUDA-compatible build is available
- Your model launch configuration includes GPU offloading settings

---

## Goal of This Project

The goal of hoboLocalLLM is to make local AI accessible to anyone.

The intended user experience is simple:

1. Start the model.
2. Upload documents.
3. Ask questions.
4. Receive answers.

No cloud infrastructure.
No API keys.
No subscriptions.
No vendor lock-in.

Just a local AI assistant that runs entirely on your own hardware.
