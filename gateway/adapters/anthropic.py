import httpx
from adapters.base import BaseAdapter
from schemas import UnifiedRequest, UnifiedResponse, UnifiedChoice, UnifiedMessage, UnifiedUsage


class AnthropicAdapter(BaseAdapter):
    model_patterns = ["claude-"]
    provider_name = "anthropic"

    async def chat_completion(self, request: UnifiedRequest) -> UnifiedResponse:
        client = await self.get_client()
        system = None
        messages = []
        for m in request.messages:
            if m.role == "system":
                system = m.content
            else:
                messages.append({"role": m.role, "content": m.content})

        body = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens or 4096,
        }
        if system:
            body["system"] = system
        if request.temperature is not None:
            body["temperature"] = request.temperature

        resp = await client.post(
            f"{self.base_url}/messages",
            json=body,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        content = data["content"][0]
        return UnifiedResponse(
            id=data["id"],
            model=data["model"],
            choices=[UnifiedChoice(
                index=0,
                message=UnifiedMessage(role="assistant", content=content.get("text", str(content))),
                finish_reason=data.get("stop_reason"),
            )],
            usage=UnifiedUsage(
                prompt_tokens=data["usage"]["input_tokens"],
                completion_tokens=data["usage"]["output_tokens"],
                total_tokens=data["usage"]["input_tokens"] + data["usage"]["output_tokens"],
            ),
            provider="anthropic",
        )

    async def health_check(self) -> bool:
        try:
            client = await self.get_client()
            resp = await client.get(
                f"{self.base_url}/models",
                headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
            )
            return resp.status_code == 200
        except Exception:
            return False


class GoogleAdapter(BaseAdapter):
    model_patterns = ["gemini-"]
    provider_name = "google"

    async def chat_completion(self, request: UnifiedRequest) -> UnifiedResponse:
        client = await self.get_client()
        contents = []
        for m in request.messages:
            role = "user" if m.role in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})

        body = {"contents": contents}
        if request.temperature is not None:
            body["generationConfig"] = {"temperature": request.temperature}
        if request.max_tokens:
            body.setdefault("generationConfig", {})["maxOutputTokens"] = request.max_tokens

        resp = await client.post(
            f"{self.base_url}/models/{request.model}:generateContent",
            json=body,
            params={"key": self.api_key},
        )
        resp.raise_for_status()
        data = resp.json()

        candidate = data["candidates"][0]
        text = candidate["content"]["parts"][0]["text"]
        return UnifiedResponse(
            id=candidate.get("finishReason", ""),
            model=request.model,
            choices=[UnifiedChoice(
                index=0,
                message=UnifiedMessage(role="assistant", content=text),
                finish_reason=candidate.get("finishReason"),
            )],
            usage=UnifiedUsage(
                prompt_tokens=data.get("usageMetadata", {}).get("promptTokenCount", 0),
                completion_tokens=data.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                total_tokens=data.get("usageMetadata", {}).get("totalTokenCount", 0),
            ),
            provider="google",
        )

    async def health_check(self) -> bool:
        try:
            client = await self.get_client()
            resp = await client.get(
                f"{self.base_url}/models",
                params={"key": self.api_key},
            )
            return resp.status_code == 200
        except Exception:
            return False
