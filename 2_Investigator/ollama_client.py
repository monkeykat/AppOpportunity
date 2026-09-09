"""Small Ollama client kept independent from Scout."""

import json
from typing import Any, Dict, Optional
from urllib.request import Request, urlopen

from config import OLLAMA_MODEL, OLLAMA_URL


class OllamaClient:
    """Call Ollama's non-streaming generate endpoint."""

    def __init__(self, url: str = OLLAMA_URL, model: str = OLLAMA_MODEL) -> None:
        self.url = url.rstrip("/")
        self.model = model

    def generate_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": schema or "json",
        }).encode("utf-8")
        request = Request(
            self.url + "/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=300) as response:
            body = json.loads(response.read().decode("utf-8"))
        generated = body.get("response") or body.get("thinking")
        if not isinstance(generated, str) or not generated.strip():
            raise ValueError("Ollama response did not contain text")
        generated = generated.strip()
        try:
            result = json.loads(generated)
        except json.JSONDecodeError:
            start = generated.find("{")
            end = generated.rfind("}")
            if start < 0 or end <= start:
                raise ValueError("Ollama response did not contain a JSON object")
            try:
                result = json.loads(generated[start:end + 1])
            except json.JSONDecodeError as error:
                raise ValueError("Ollama response contained invalid JSON") from error
        if not isinstance(result, dict):
            raise ValueError("Ollama response was not a JSON object")
        return result