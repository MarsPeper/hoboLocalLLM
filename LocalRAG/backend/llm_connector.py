import json
import logging
import httpx
from typing import List, Dict, Any, Generator

logger = logging.getLogger(__name__)

class LLMConnector:
    def __init__(self, api_url: str = "http://localhost:8080/v1", model_name: str = "local-model"):
        self.api_url = api_url.rstrip('/')
        self.model_name = model_name

    def generate_response(self, system_prompt: str, user_question: str, temperature: float = 0.1, max_tokens: int = 1024) -> str:
        """Call the local LLM endpoint synchronously (non-streaming)."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ]
        
        try:
            logger.info(f"Sending LLM request to {self.api_url}/chat/completions...")
            response = httpx.post(
                f"{self.api_url}/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False
                },
                timeout=120.0
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error calling local LLM API: {e}")
            return f"Error connecting to local LLM server at {self.api_url}. Please ensure that the llama-server is started and running correctly. Details: {str(e)}"

    def generate_response_stream(self, system_prompt: str, user_question: str, temperature: float = 0.1, max_tokens: int = 1024) -> Generator[str, None, None]:
        """Calls the local LLM endpoint and yields response tokens as they arrive."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ]
        
        try:
            logger.info(f"Sending streaming LLM request to {self.api_url}/chat/completions...")
            
            with httpx.Client() as client:
                with client.stream(
                    "POST",
                    f"{self.api_url}/chat/completions",
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stream": True
                    },
                    timeout=120.0
                ) as response:
                    if response.status_code != 200:
                        yield f"Error: LLM server responded with status code {response.status_code}."
                        return

                    for line in response.iter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk_json = json.loads(data_str)
                                content = chunk_json["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Error in LLM stream: {e}")
            yield f"\n[Error communicating with local LLM server at {self.api_url}: {str(e)}. Please check if your llama-server is running.]"
