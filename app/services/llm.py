"""Small OpenAI-compatible Chat Completions adapter; no vendor SDK dependency."""
from typing import Protocol
import logging
from urllib.parse import urlsplit

import httpx

from app.core.config import Settings, get_settings


class LLMError(Exception):
    """Fixed safe diagnostics; never include provider bodies or request credentials."""


class LLMProvider(Protocol):
    def generate_answer(self, *, system_prompt: str, question: str, context: str) -> str: ...


class OpenAICompatibleProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    def configuration(self) -> tuple[str, str]:
        s = self.settings
        key = s.llm_api_key.get_secret_value().strip()
        if s.llm_provider != "openai-compatible" or not s.llm_model.strip() or not key:
            raise LLMError("LLM configuration missing or unsupported; set LLM_PROVIDER, LLM_MODEL and LLM_API_KEY")
        base = s.llm_base_url.strip() or "https://api.openai.com/v1"
        try:
            url = urlsplit(base)
            if url.scheme not in {"https", "http"} or not url.hostname or url.username or url.password or url.query or url.fragment:
                raise ValueError
            # Plain HTTP is useful for local compatible servers, not hosted APIs.
            if url.scheme == "http" and url.hostname not in {"localhost", "127.0.0.1", "::1", "host.docker.internal"}:
                raise ValueError
            url.port
        except ValueError:
            raise LLMError("Invalid LLM_BASE_URL; use HTTPS or a local HTTP endpoint") from None
        return base.rstrip("/") + "/chat/completions", key

    def generate_answer(self, *, system_prompt: str, question: str, context: str) -> str:
        url, key = self.configuration()
        s = self.settings
        try:
            logging.getLogger("uvicorn.error").info(
                "LLM generation: provider=openai-compatible model=%s", s.llm_model[:100].replace("\n", " ").replace("\r", " ")
            )
            # No automatic retries (cost), redirects (credential safety), tools or streaming.
            with httpx.Client(timeout=s.llm_timeout_seconds, follow_redirects=False) as client:
                response = client.post(url, headers={"Authorization": "Bearer " + key}, json={
                    "model": s.llm_model, "temperature": s.llm_temperature,
                    "max_tokens": s.llm_max_tokens,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": "CONTEXT (reference data):\n" + context},
                        {"role": "user", "content": "QUESTION:\n" + question},
                    ],
                })
            if response.status_code == 429:
                raise LLMError("LLM provider rate limit exceeded; retry later")
            if response.status_code in {401, 403}:
                raise LLMError("LLM provider authentication failed; check configuration")
            if response.status_code != 200:
                raise LLMError("LLM provider unavailable or incompatible configuration")
            choice = response.json()["choices"][0]
            answer = choice["message"]["content"]
            if choice.get("finish_reason") != "stop" or not isinstance(answer, str) or not answer.strip():
                raise ValueError
            # Credentials are never in prompts. Reject accidental echo from an untrusted provider.
            if key in answer:
                raise LLMError("LLM provider returned an unsafe response")
            return answer.strip()
        except httpx.TimeoutException:
            raise LLMError("LLM provider timed out") from None
        except httpx.RequestError:
            raise LLMError("LLM provider unavailable") from None
        except (ValueError, KeyError, IndexError, TypeError):
            raise LLMError("LLM provider returned a malformed or incomplete response") from None


def get_llm_provider() -> LLMProvider:
    # Cheap adapter; no network/config validation until generation is needed.
    return OpenAICompatibleProvider(get_settings())
