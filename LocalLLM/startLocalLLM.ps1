conda activate LocalLLM

llama-server `
  -m "{path_to_model}" `
  -c 8192 `
  -ngl 999 `
  --host 0.0.0.0 `
  --port 8080