import httpx
from adapters.base import BaseAdapter
from schemas import UnifiedRequest, UnifiedResponse, UnifiedChoice, UnifiedMessage, UnifiedUsage


class OpenAIAdapter(BaseAdapter):
    model_patterns = ["gpt-", "o1-", "o3-"]
    provider_name = "openai"

    async def chat_completion(self, request: UnifiedRequest) -> UnifiedResponse:
        client = await self.get_client()
        body = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": False,
        }
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens

        resp = await client.post(
            f"{self.base_url}/chat/completions",
            json=body,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()

        return UnifiedResponse(
            id=data["id"],
            model=data["model"],
            choices=[
                UnifiedChoice(
                    index=c["index"],
                    message=UnifiedMessage(
                        role=c["message"]["role"],
                        content=c["message"]["content"],
                    ),
                    finish_reason=c.get("finish_reason"),
                )
                for c in data["choices"]
            ],
            usage=UnifiedUsage(
                prompt_tokens=data["usage"]["prompt_tokens"],
                completion_tokens=data["usage"]["completion_tokens"],
                total_tokens=data["usage"]["total_tokens"],
            ),
            provider="openai",
        )

    async def health_check(self) -> bool:
        try:
            client = await self.get_client()
            resp = await client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            return resp.status_code == 200
        except Exception:
            return False
