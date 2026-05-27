import json
from typing import Any

from groq import Groq

from pr_sentinel.core.config import get_settings
from pr_sentinel.llm.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


class LlmClientError(Exception):
    pass


class LlmClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.provider = settings.llm_provider.lower()
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model

    def is_enabled(self) -> bool:
        return self.provider != "disabled" and bool(self.api_key)

    def review(self, context: dict[str, Any]) -> dict[str, Any]:
        if not self.is_enabled():
            return {
                "findings": [],
                "ai_adjustment": 0,
                "ai_adjustment_reasons": [],
            }

        if self.provider != "groq":
            raise LlmClientError(f"Unsupported LLM provider: {self.provider}")

        return self._review_with_groq(context)

    def _review_with_groq(self, context: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise LlmClientError("LLM_API_KEY is missing")

        client = Groq(api_key=self.api_key)
        context_json = json.dumps(context, ensure_ascii=False, indent=2)

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(context_json=context_json),
                },
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content

        if not content:
            raise LlmClientError("LLM returned empty response")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LlmClientError(f"LLM returned invalid JSON: {content}") from exc

        if not isinstance(parsed, dict):
            raise LlmClientError("LLM response was not a JSON object")

        return parsed