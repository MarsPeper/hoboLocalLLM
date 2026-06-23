import os
import sys
import time
import yaml
from typing import List, Dict, Any

# Ensure imports resolve from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from document_processor import process_document
from embeddings_manager import EmbeddingsManager
from vector_store import VectorStore
from llm_connector import LLMConnector

# Mock documents to ingest for benchmarking
MOCK_DOCS = {
    "quantum_computing.txt": (
        "Quantum computing is a multidisciplinary field comprising aspects of computer science, "
        "physics, and mathematics that utilizes quantum mechanics to solve complex problems faster "
        "than on classical computers. The basic unit of information in quantum computing is the qubit. "
        "Qubits can exist in a state of superposition, meaning they can represent a 0, a 1, or any "
        "quantum proportion of both simultaneously. Another key principle is entanglement, which allows "
        "qubits that are shared spatially to behave in unison. IBM's quantum processors use superconducting "
        "transmon qubits, whereas IonQ uses trapped ion technologies. A major bottleneck in quantum computing "
        "is decoherence, where environmental noise disrupts the quantum state, causing computational errors."
    ),
    "project_aurora.txt": (
        "Project Aurora is an internal aerospace initiative aimed at developing next-generation electric VTOL "
        "(Vertical Take-Off and Landing) drones for urban logistics. The initiative was started in January 2025. "
        "The current prototype, Aurora-V4, runs on a dual-redundant lithium-sulfur battery pack with a capacity of "
        "180 Wh/kg. The drone uses eight independent carbon-fiber rotors driven by brushless DC motors. "
        "The maximum payload capacity is 25 kilograms, and it has an autonomous range of 45 kilometers "
        "at a cruising speed of 60 km/h. The autopilot software is based on PX4 with a custom obstacle avoidance "
        "module written in Rust called 'Shield-V1'. Project lead is Dr. Elena Rostova."
    )
}

# Evaluation queries and ground truth tests
BENCHMARK_CASES = [
    {
        "id": 1,
        "name": "Fact Retrieval & Generation - Specific Name",
        "query": "Who is the project lead of Project Aurora?",
        "expected_keywords": ["Elena", "Rostova"],
        "expect_answer": True
    },
    {
        "id": 2,
        "name": "Fact Retrieval & Generation - Technical Number",
        "query": "What is the range and payload capacity of the Aurora-V4 drone?",
        "expected_keywords": ["45", "range", "25", "payload"],
        "expect_answer": True
    },
    {
        "id": 3,
        "name": "Fact Retrieval & Generation - Conceptual Term",
        "query": "What is decoherence in quantum computing?",
        "expected_keywords": ["noise", "disrupt", "state", "error"],
        "expect_answer": True
    },
    {
        "id": 4,
        "name": "Negative Control - Off-Context / Hallucination Check",
        "query": "What is the capital of France and what is its primary import?",
        "expected_keywords": ["France"],
        "expect_answer": False, # Expect "I do not have enough information"
        "insufficient_info_trigger": "I do not have enough information"
    }
]


def run_benchmark():
    print("====================================================")
    print("  LocalRAG Model Benchmarking & Quality Evaluation  ")
    print("====================================================")

    # 1. Load active config
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(backend_dir, "config.yaml")
    
    if not os.path.exists(config_path):
        print(f"Error: config.yaml not found at {config_path}")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Extract configs
    rag_conf = config.get("rag", {})
    emb_conf = config.get("embedding", {})
    qdrant_conf = config.get("qdrant", {})
    llm_conf = config.get("llm", {})

    print(f"\nActive LLM Endpoint:    {llm_conf.get('api_url')}")
    print(f"Active LLM Model ID:   {llm_conf.get('model_name')}")
    print(f"Active Dense Embedder: {emb_conf.get('model_name')}")
    print(f"Active Sparse Embedder:{emb_conf.get('sparse_model_name')}")
    print(f"Hybrid Search Enabled: {rag_conf.get('use_hybrid_search')}")
    print(f"Reranker Enabled:      {rag_conf.get('use_reranker')} ({rag_conf.get('reranker_model')})")

    # 2. Re-initialize temporary benchmark collection in Qdrant
    print("\n[1/3] Preparing temporary benchmark vector store...")
    emb_manager = EmbeddingsManager(
        model_name=emb_conf.get("model_name", "all-MiniLM-L6-v2"),
        sparse_model_name=emb_conf.get("sparse_model_name", "Qdrant/bm25"),
        device="cpu",
        api_url=llm_conf.get("api_url")
    )
    
    # We write to a benchmark collection
    bench_collection = "benchmark_eval_collection"
    vector_store = VectorStore(
        collection_name=bench_collection,
        dense_embeddings=emb_manager.dense_embeddings,
        sparse_embeddings=emb_manager.sparse_embeddings,
        path=os.path.join(backend_dir, "qdrant_db"),
        use_hybrid_search=rag_conf.get("use_hybrid_search", True)
    )
    
    # Reset it
    vector_store.client.delete_collection(bench_collection)
    vector_store._ensure_collection()

    # 3. Create mock files and ingest them
    temp_files = []
    try:
        for file_name, content in MOCK_DOCS.items():
            path = os.path.join(backend_dir, file_name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            temp_files.append(path)

            print(f"  Ingesting mock file: {file_name}...")
            docs = process_document(path, chunk_size=300, chunk_overlap=30)
            vector_store.add_documents(docs)
            
        print("  Ingestion complete.")

    except Exception as e:
        print(f"Error during benchmark ingestion: {e}")
        # cleanup
        _cleanup(temp_files)
        return

    # 4. Initialize LLM Connector
    llm_connector = LLMConnector(
        api_url=llm_conf.get("api_url"),
        model_name=llm_conf.get("model_name")
    )

    # 5. Run tests
    print("\n[2/3] Running evaluation queries against LLM...")
    results = []

    for case in BENCHMARK_CASES:
        print(f"\nTest #{case['id']}: {case['name']}")
        print(f"  Query: \"{case['query']}\"")
        
        # Retrieval
        start_time = time.time()
        sources = vector_store.search_similar(
            query=case['query'],
            top_k=rag_conf.get("top_k", 4),
            use_reranker=rag_conf.get("use_reranker", True),
            reranker_model=rag_conf.get("reranker_model", "ms-marco-MiniLM-L-12-v2"),
            base_retrieve_k=rag_conf.get("base_retrieve_k", 12)
        )
        retrieve_duration = time.time() - start_time
        print(f"  Retrieved {len(sources)} source chunks in {retrieve_duration:.3f}s")
        
        # Build prompt
        context_blocks = []
        for src in sources:
            context_blocks.append(f"Source: {src['file_name']}:\n{src['content']}")
        context_str = "\n\n".join(context_blocks) if context_blocks else "No relevant context found."
        
        system_prompt_template = llm_conf.get("system_prompt", "")
        formatted_system_prompt = system_prompt_template.replace("{context}", context_str).replace("{question}", case['query'])

        # Generate response and track metrics
        tokens = []
        ttft = 0.0 # Time to First Token
        gen_start = time.time()
        
        try:
            stream = llm_connector.generate_response_stream(
                system_prompt=formatted_system_prompt,
                user_question=case['query'],
                temperature=llm_conf.get("temperature", 0.1),
                max_tokens=llm_conf.get("max_tokens", 512)
            )
            
            for chunk in stream:
                if len(tokens) == 0:
                    ttft = time.time() - gen_start
                tokens.append(chunk)
                
            gen_duration = time.time() - gen_start
            full_response = "".join(tokens).strip()
            total_tokens = len(full_response.split()) # approximation of token count
            tokens_per_sec = total_tokens / gen_duration if gen_duration > 0 else 0.0
            
            print(f"  Time to First Token (TTFT): {ttft:.3f}s")
            print(f"  Tokens per Second:           {tokens_per_sec:.1f} tok/s")
            print(f"  Response: \"{full_response[:100]}...\"")

            # Evaluate quality
            # Faithfulness check
            passed_quality = True
            failure_reason = ""
            
            if case["expect_answer"]:
                missing_keywords = [kw for kw in case["expected_keywords"] if kw.lower() not in full_response.lower()]
                if missing_keywords:
                    passed_quality = False
                    failure_reason = f"Answer missing key facts: {missing_keywords}"
            else:
                # Expecting 'insufficient info' fallback
                trigger = case.get("insufficient_info_trigger", "I do not have enough information")
                if trigger.lower() not in full_response.lower():
                    passed_quality = False
                    failure_reason = "Model failed negative control check (did not refuse to answer off-context question)."

            if passed_quality:
                print("  Quality Status: [PASSED]")
            else:
                print(f"  Quality Status: [FAILED] - {failure_reason}")

            results.append({
                "id": case["id"],
                "name": case["name"],
                "ttft": ttft,
                "tps": tokens_per_sec,
                "passed_quality": passed_quality,
                "reason": failure_reason
            })

        except Exception as eval_err:
            print(f"  Generation failed: {eval_err}")
            results.append({
                "id": case["id"],
                "name": case["name"],
                "ttft": 0.0,
                "tps": 0.0,
                "passed_quality": False,
                "reason": f"Execution error: {eval_err}"
            })

    # Cleanup temp collection and files
    _cleanup(temp_files)
    vector_store.client.delete_collection(bench_collection)

    # 6. Display final summary report
    print("\n[3/3] Benchmark Summary Report:")
    print("--------------------------------------------------------------------------------")
    print(f"{'Test ID':<8} | {'Benchmark Case Name':<42} | {'TTFT':<7} | {'TPS':<7} | {'Status':<8}")
    print("--------------------------------------------------------------------------------")
    
    total_tps = 0.0
    total_ttft = 0.0
    passed_count = 0
    
    for res in results:
        status_str = "PASS" if res["passed_quality"] else "FAIL"
        print(f"{res['id']:<8} | {res['name']:<42} | {res['ttft']:>5.2f}s | {res['tps']:>5.1f}/s | {status_str:<8}")
        
        if res["passed_quality"]:
            passed_count += 1
        total_tps += res["tps"]
        total_ttft += res["ttft"]

    avg_tps = total_tps / len(results) if results else 0.0
    avg_ttft = total_ttft / len(results) if results else 0.0
    quality_score = (passed_count / len(results)) * 100 if results else 0.0

    print("--------------------------------------------------------------------------------")
    print(f"Average Time to First Token (TTFT): {avg_ttft:.2f} seconds")
    print(f"Average Generation Throughput (TPS): {avg_tps:.1f} tokens/second")
    print(f"System Accuracy & Refusal Score:    {quality_score:.1f}% ({passed_count}/{len(results)} cases passed)")
    print("--------------------------------------------------------------------------------")
    
    if avg_tps < 5.0:
        print("Recommendation: Model throughput is low (< 5 tok/s). Try a smaller model (e.g. 1.5B or 3B parameters) or configure GPU offloading.")
    elif quality_score < 75.0:
        print("Recommendation: Accuracy is low (< 75%). Make sure context retrieval is set up properly or select a more instruct-aligned model.")
    else:
        print("Recommendation: Model is performing exceptionally well on this hardware configuration!")
    print("====================================================")


def _cleanup(paths):
    for p in paths:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass


if __name__ == "__main__":
    run_benchmark()
