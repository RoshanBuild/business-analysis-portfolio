from __future__ import annotations
import json
import urllib.request
import urllib.error
from typing import Type
from pydantic import BaseModel

class OllamaAdapter:
    def __init__(self, model: str, base_url: str = "http://localhost:11434", temperature: float = 0):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature

    def parse(self, messages: list[dict], schema: Type[BaseModel]):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": schema.model_json_schema(),
            "options": {"temperature": self.temperature},
        }
        req = urllib.request.Request(
            self.base_url + "/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type":"application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise RuntimeError(
                "Cannot connect to local Ollama. Start Ollama and ensure the model is installed. "
                f"Underlying error: {e}"
            ) from e
        content = data.get("message",{}).get("content","")
        if not content:
            raise RuntimeError("Ollama returned no message content.")
        parsed = schema.model_validate_json(content)
        meta = {
            "model": data.get("model", self.model),
            "done_reason": data.get("done_reason"),
            "prompt_eval_count": data.get("prompt_eval_count"),
            "eval_count": data.get("eval_count"),
            "total_duration_ns": data.get("total_duration"),
        }
        return parsed, meta
