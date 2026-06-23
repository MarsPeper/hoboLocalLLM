import logging
from typing import Generator
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class LLMConnector:
    """
    LangChain LLM connector that interfaces with local OpenAI-compatible chat completion
    endpoints (e.g. llama-server, Ollama, LM Studio).
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8080/v1",
        model_name: str = "local-model"
    ):
        self.api_url = api_url.rstrip("/")
        self.model_name = model_name

    def generate_response(
        self,
        system_prompt: str,
        user_question: str,
        temperature: float = 0.1,
        max_tokens: int = 1024
    ) -> str:
        """Invokes the local LLM and returns the completed text string."""
        logger.info(f"Invoking ChatOpenAI (non-stream) at {self.api_url}/chat/completions...")
        try:
            llm = ChatOpenAI(
                base_url=self.api_url,
                api_key="not-needed",
                model=self.model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_question)
            ]
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"LangChain LLM call failed: {e}")
            return (
                f"Error connecting to local LLM server at {self.api_url}.\n"
                f"Make sure your llama-server or LLM model provider is running.\n"
                f"Details: {str(e)}"
            )

    def generate_response_stream(
        self,
        system_prompt: str,
        user_question: str,
        temperature: float = 0.1,
        max_tokens: int = 1024
    ) -> Generator[str, None, None]:
        """Streams response tokens from the local LLM using LangChain."""
        logger.info(f"Invoking ChatOpenAI (streaming) at {self.api_url}/chat/completions...")
        try:
            llm = ChatOpenAI(
                base_url=self.api_url,
                api_key="not-needed",
                model=self.model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=True
            )
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_question)
            ]
            for chunk in llm.stream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"LangChain LLM streaming failed: {e}")
            yield (
                f"\n[Error streaming from local LLM server at {self.api_url}. "
                f"Is llama-server running? Details: {str(e)}]"
            )