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

    async def get_balance(self) -> dict | None:
        try:
            from datetime import datetime, timezone
            from adapters.balance_utils import try_balance_endpoints
            client = await self.get_client()
            result = await try_balance_endpoints(client, self.api_key, self.base_url)
            if result:
                return result
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            resp = await client.get(
                f"{self.base_url}/organization/costs?start_date={today}&end_date={today}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                total = sum(
                    float(line.get("line_item", {}).get("amount", 0) or 0)
                    for line in data.get("data", [])
                )
                return {"balance": total, "currency": "USD"}
        except Exception:
            pass
        return None

    async def health_check(self) -> bool:
        try:
            client = await self.get_client()
            # Try /v1/models first (OpenAI standard), then /models
            for path in ("/v1/models", "/models"):
                try:
                    resp = await client.get(
                        f"{self.base_url}{path}",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                    )
                    if resp.status_code == 200:
                        return True
                except Exception:
                    continue
            return False
        except Exception:
            return False
