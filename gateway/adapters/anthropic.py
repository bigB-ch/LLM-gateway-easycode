import httpx
from adapters.base import BaseAdapter
from schemas import UnifiedRequest, UnifiedResponse, UnifiedChoice, UnifiedMessage, UnifiedUsage


class AnthropicAdapter(BaseAdapter):
    model_patterns = ["claude-"]
    provider_name = "anthropic"

    def _build_anthropic_body(self, request: UnifiedRequest) -> dict:
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
        return body

    def _auth_headers(self) -> dict:
        return {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}

    async def chat_completion(self, request: UnifiedRequest) -> UnifiedResponse:
        client = await self.get_client()
        body = self._build_anthropic_body(request)
        resp = await client.post(
            f"{self.base_url}/messages",
            json=body,
            headers=self._auth_headers(),
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

    async def stream_completion(self, request: UnifiedRequest):
        """Stream using Anthropic SSE format. Yields (text_delta, finish_reason, usage_dict)."""
        import json as _json
        client = await self.get_client()
        body = self._build_anthropic_body(request)
        body["stream"] = True

        prompt_tokens = 0
        completion_tokens = 0
        finish_reason = None

        async with client.stream(
            "POST",
            f"{self.base_url}/messages",
            json=body,
            headers=self._auth_headers(),
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                try:
                    event = _json.loads(data_str)
                except _json.JSONDecodeError:
                    continue

                etype = event.get("type", "")
                if etype == "content_block_delta":
                    delta = event.get("delta", {})
                    text = delta.get("text", "")
                    if text:
                        yield (text, None, None)
                elif etype == "message_delta":
                    delta = event.get("delta", {})
                    finish_reason = delta.get("stop_reason")
                    usage = event.get("usage", {})
                    prompt_tokens = usage.get("input_tokens", 0)
                    completion_tokens = usage.get("output_tokens", 0)

        yield (None, finish_reason, {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        })

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


class XunfeiAdapter(BaseAdapter):
    """Xunfei MaaS adapter — Anthropic-format API with Bearer auth."""
    model_patterns = ["xunfei-"]
    provider_name = "xunfei"

    _MODEL_MAP = {
        "xunfei-qwen": "xopqwen36v35b",
    }

    def _upstream_model(self, model: str) -> str:
        return self._MODEL_MAP.get(model, model)

    def _build_anthropic_body(self, request: UnifiedRequest) -> dict:
        system = None
        messages = []
        for m in request.messages:
            if m.role == "system":
                system = m.content
            else:
                messages.append({"role": m.role, "content": m.content})
        body = {
            "model": self._upstream_model(request.model),
            "messages": messages,
            "max_tokens": request.max_tokens or 4096,
        }
        if system:
            body["system"] = system
        if request.temperature is not None:
            body["temperature"] = request.temperature
        return body

    async def chat_completion(self, request: UnifiedRequest) -> UnifiedResponse:
        client = await self.get_client()
        body = self._build_anthropic_body(request)
        resp = await client.post(
            f"{self.base_url}/messages",
            json=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
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
            provider="xunfei",
        )

    async def stream_completion(self, request: UnifiedRequest):
        """Stream using Anthropic SSE format. Yields (text_delta, finish_reason, usage_dict)."""
        import json
        client = await self.get_client()
        body = self._build_anthropic_body(request)
        body["stream"] = True

        prompt_tokens = 0
        completion_tokens = 0
        finish_reason = None

        async with client.stream(
            "POST",
            f"{self.base_url}/messages",
            json=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "anthropic-version": "2023-06-01",
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                try:
                    event = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                etype = event.get("type", "")
                if etype == "content_block_delta":
                    delta = event.get("delta", {})
                    text = delta.get("text", "")
                    if text:
                        yield (text, None, None)
                elif etype == "message_delta":
                    delta = event.get("delta", {})
                    finish_reason = delta.get("stop_reason")
                    usage = event.get("usage", {})
                    prompt_tokens = usage.get("input_tokens", 0)
                    completion_tokens = usage.get("output_tokens", 0)

        yield (None, finish_reason, {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        })

    async def health_check(self) -> bool:
        try:
            client = await self.get_client()
            resp = await client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}", "anthropic-version": "2023-06-01"},
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
