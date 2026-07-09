conda activate LocalLLM

llama-server `
  -m "C:\LLMModels\Phi-4-mini-instruct.Q8_0.gguf" `
  -c 8192 `
  -ngl 999 `
  --host 0.0.0.0 `
  --port 8080