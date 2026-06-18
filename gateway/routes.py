import uuid
import json
import time
import random
import asyncio
from fastapi import APIRouter, Request, HTTPException

from schemas import UnifiedRequest
from middleware.auth import verify_api_key
from middleware.ratelimit import check_rate_limit
from adapters import find_adapter
from circuit_breaker import should_attempt, record_success, record_failure
from pricing import calculate_cost
from config import CIRCUIT_BREAKER_CONFIG, UPSTREAM_TIMEOUT, MAX_RETRIES, RETRY_BACKOFF_BASE
from redis_client import redis

router = APIRouter(prefix="/v1")

_adapters = []


def set_adapters(adapters):
    global _adapters
    _adapters = adapters


def get_adapters():
    return _adapters


# ── Anthropic-compatible endpoint (for Claude Code etc.) ──

@router.post("/messages")
async def anthropic_messages(request: Request):
    # 1. Auth (Anthropic uses x-api-key header)
    auth_info = await verify_api_key(request, allow_anthropic_auth=True)
    user_id = auth_info["user_id"]
    rate_limit = auth_info["rate_limit"]
    key_prefix = auth_info.get("key_prefix", "")

    # 2. Rate limit
    await check_rate_limit(user_id, rate_limit)
    client_ip = request.client.host if request.client else "unknown"

    # 3. Parse Anthropic request
    body = await request.json()
    model = body.get("model", "")
    print(f"[DEBUG] anthropic_messages: stream={body.get('stream', False)}, model={body.get('model','')}, key_prefix={key_prefix}, raw_model={model}")
    messages_raw = body.get("messages", [])
    max_tokens = body.get("max_tokens", 4096)
    temperature = body.get("temperature")
    system = body.get("system")

    # Map Anthropic model names to available backend models
    # Strip version suffix (e.g. claude-sonnet-4-6-20251001 → claude-sonnet-4-6)
    import re as _re
    _base_model = _re.sub(r'-\d{8}$', '', model)
    _ANTHROPIC_MODEL_MAP = {
        "claude-opus-4-7": "deepseek-v4-pro",
        "claude-opus-4-5": "deepseek-v4-pro",
        "claude-sonnet-4-6": "deepseek-v4-flash",
        "claude-sonnet-4-5": "deepseek-v4-flash",
        "claude-haiku-4-5": "deepseek-v4-flash",
        "claude-3-5-haiku": "deepseek-v4-flash",
    }
    model = _ANTHROPIC_MODEL_MAP.get(_base_model, model)

    # Convert to internal format
    from schemas import UnifiedRequest, UnifiedMessage
    unified_messages = []
    if system:
        # Anthropic system can be string or array of text blocks
        if isinstance(system, list):
            system_text = "\n".join(
                b.get("text", "") for b in system if b.get("type") == "text"
            )
        else:
            system_text = system
        if system_text:
            unified_messages.append(UnifiedMessage(role="system", content=system_text))
    for m in messages_raw:
        role = m.get("role", "user")
        content = m.get("content", "")
        # Anthropic format: content can be a string or array of content blocks
        if isinstance(content, list):
            # Extract text from the first text block
            text_parts = [b.get("text", "") for b in content if b.get("type") == "text"]
            content = "\n".join(text_parts) if text_parts else ""
        unified_messages.append(UnifiedMessage(role=role, content=content))

    unified = UnifiedRequest(
        model=model,
        messages=unified_messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    request_id = f"req_{uuid.uuid4().hex[:16]}"
    t_start = time.time()

    is_stream = body.get("stream", False)

    # 4. Find adapter (skip model allowlist for Anthropic endpoint —
    #    Claude Code model names don't match backend model names)
    adapter = find_adapter(model, _adapters)
    if adapter is None:
        raise HTTPException(status_code=400, detail={"error": "invalid_model"})

    # 5. Circuit breaker
    cb_config = CIRCUIT_BREAKER_CONFIG.get(
        adapter.provider_name,
        {"failure_threshold": 3, "timeout_seconds": 30, "half_open_ttl": 30},
    )
    if not await should_attempt(adapter.provider_name, cb_config):
        raise HTTPException(status_code=503, detail={"error": "model_temporarily_unavailable"})

    # 6. Balance check
    user_balance = auth_info.get("balance", 0)
    has_plans = auth_info.get("has_plans", False)
    if user_balance <= 0 and not has_plans:
        raise HTTPException(status_code=402, detail={"error": "insufficient_balance"})

    # 7. Streaming path
    if is_stream:
        print(f"[DEBUG] anthropic_messages: STREAMING path for {request_id}, adapter={adapter.provider_name}")
        from fastapi.responses import StreamingResponse

        async def stream_anthropic():
            prompt_tokens = 0
            completion_tokens = 0
            finish_reason = None
            stream_error = None
            msg_id = f"msg_{request_id}"

            # -- Direct passthrough for DeepSeek Anthropic API --
            if adapter.provider_name == "deepseek":
                from httpx import AsyncClient
                anthro_base = adapter.base_url.rstrip("/").replace("/v1", "/anthropic/v1") + "/messages"

                # Use original messages directly to preserve tool_use/tool_result/thinking blocks
                ds_messages = [m for m in messages_raw if m.get("role") != "system"]
                ds_body = {
                    "model": _base_model,
                    "messages": ds_messages,
                    "max_tokens": unified.max_tokens or 4096,
                    "stream": True,
                }
                if system:
                    if isinstance(system, str):
                        ds_body["system"] = system
                    elif isinstance(system, list):
                        ds_body["system"] = "\n".join(b.get("text", "") for b in system if b.get("type") == "text")
                if unified.temperature is not None:
                    ds_body["temperature"] = unified.temperature
                # Forward optional fields from original request
                for field in ("thinking", "tools", "tool_choice", "top_p", "top_k", "stop_sequences", "metadata"):
                    if body.get(field) is not None:
                        ds_body[field] = body[field]

                ds_headers = {
                    "x-api-key": adapter.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                    "Accept-Encoding": "identity",
                }
                # Forward anthropic-beta header from original request
                beta = request.headers.get("anthropic-beta")
                if beta:
                    ds_headers["anthropic-beta"] = beta

                try:
                    async with AsyncClient(timeout=120.0) as client:
                        async with client.stream("POST", anthro_base, json=ds_body, headers=ds_headers) as resp:
                            resp.raise_for_status()
                            async for line in resp.aiter_lines():
                                # Intercept message_start to restore original model name
                                if line.startswith("data: ") and '"message_start"' in line:
                                    try:
                                        ev = __import__('json').loads(line[6:])
                                        if ev.get("type") == "message_start":
                                            msg = ev.get("message", {})
                                            if msg.get("model") and _base_model:
                                                msg["model"] = _base_model
                                            line = "data: " + __import__('json').dumps(ev, ensure_ascii=False)
                                    except Exception:
                                        pass

                                # Extract token counts from DeepSeek events
                                if line.startswith("data: "):
                                    try:
                                        ev = __import__('json').loads(line[6:])
                                        if ev.get("type") == "message_start":
                                            u = ev.get("message", {}).get("usage", {})
                                            prompt_tokens = u.get("input_tokens", 0)
                                        elif ev.get("type") == "message_delta":
                                            u = ev.get("usage", {})
                                            completion_tokens = u.get("output_tokens", 0)
                                    except Exception:
                                        pass

                                # Yield line immediately without buffering for low latency
                                yield line + "\n"
                except Exception as e:
                    stream_error = str(e)

                t_end = time.time()
                latency_ms = int((t_end - t_start) * 1000)
                if prompt_tokens or completion_tokens:
                    cost, bill_cost = await calculate_cost(model, prompt_tokens, completion_tokens)
                else:
                    cost, bill_cost = 0, 0

                if stream_error:
                    await record_failure(adapter.provider_name, cb_config)
                else:
                    await record_success(adapter.provider_name)

                log_entry = {
                    "request_id": request_id, "user_id": user_id,
                    "api_key_prefix": key_prefix, "model": model,
                    "provider": adapter.provider_name,
                    "prompt_tokens": str(prompt_tokens),
                    "completion_tokens": str(completion_tokens),
                    "cost": str(cost), "bill_cost": str(bill_cost),
                    "latency_ms": str(latency_ms),
                    "status": "error" if stream_error else "success",
                    "error_msg": stream_error or "",
                    "ip": client_ip,
                }
                await redis.xadd("usage_log_stream", log_entry)
                return

            # Track content block state
            blocks_started = False
            active_block_type = None  # "thinking" or "text"
            block_index = -1

            def _close_block():
                nonlocal active_block_type, block_index
                if active_block_type is None:
                    return []
                events = []
                if active_block_type == "thinking":
                    # Extended thinking protocol: signature_delta before block_stop
                    events.append(f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': block_index, 'delta': {'type': 'signature_delta', 'signature': msg_id}})}\n\n")
                events.append(f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': block_index})}\n\n")
                active_block_type = None
                return events

            try:
                async for item, fr, usage in adapter.stream_completion(unified):
                    # Normalize: plain string (backward compat) or dict with type/text
                    if isinstance(item, dict):
                        chunks = [item]
                    elif item:
                        chunks = [{"type": "text", "text": item}]
                    else:
                        chunks = []

                    for chunk in chunks:
                        ctype = chunk.get("type", "text")
                        ctext = chunk.get("text", "")
                        if not ctext:
                            continue

                        if not blocks_started:
                            blocks_started = True
                            yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': msg_id, 'type': 'message', 'role': 'assistant', 'model': unified.model, 'content': [], 'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"

                        if ctype != active_block_type:
                            close = _close_block()
                            if close:
                                yield close
                            block_index += 1
                            if ctype == "thinking":
                                cb = {"type": "thinking", "thinking": "", "signature": ""}
                            else:
                                cb = {"type": "text", "text": ""}
                            yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': block_index, 'content_block': cb})}\n\n"
                            active_block_type = ctype

                        if ctype == "thinking":
                            yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': block_index, 'delta': {'type': 'thinking_delta', 'thinking': ctext}})}\n\n"
                        else:
                            yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': block_index, 'delta': {'type': 'text_delta', 'text': ctext}})}\n\n"

                    if fr:
                        finish_reason = fr
                    if usage:
                        prompt_tokens = usage.get("prompt_tokens", 0)
                        completion_tokens = usage.get("completion_tokens", 0)

                if blocks_started:
                    for event in _close_block():
                        yield event
                    yield f"event: message_delta\ndata: {json.dumps({'type': 'message_delta', 'delta': {'stop_reason': finish_reason or 'end_turn', 'stop_sequence': None}, 'usage': {'output_tokens': completion_tokens}})}\n\n"
                    yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"

                # After stream: write usage log and deduct
                t_end = time.time()
                latency_ms = int((t_end - t_start) * 1000)
                if prompt_tokens or completion_tokens:
                    cost, bill_cost = await calculate_cost(model, prompt_tokens, completion_tokens)
                else:
                    cost, bill_cost = 0, 0
                await record_success(adapter.provider_name)
                log_entry = {
                    "request_id": request_id, "user_id": user_id,
                    "api_key_prefix": key_prefix, "model": model,
                    "provider": adapter.provider_name,
                    "prompt_tokens": str(prompt_tokens),
                    "completion_tokens": str(completion_tokens),
                    "cost": str(cost), "bill_cost": str(bill_cost),
                    "latency_ms": str(latency_ms),
                    "status": "success", "error_msg": "",
                    "ip": client_ip,
                }
                await redis.xadd("usage_log_stream", log_entry)

            except NotImplementedError:
                # Fallback: adapter doesn't support native streaming, try OpenAI-compat path
                from httpx import AsyncClient
                fallback_client = AsyncClient(timeout=120.0)
                try:
                    msgs = [{"role": m.role, "content": m.content} for m in unified.messages]
                    stream_body = {
                        "model": unified.model,
                        "messages": msgs,
                        "stream": True,
                    }
                    if unified.max_tokens:
                        stream_body["max_tokens"] = unified.max_tokens
                    if unified.temperature is not None:
                        stream_body["temperature"] = unified.temperature

                    async with fallback_client.stream(
                        "POST",
                        f"{adapter.base_url}/chat/completions",
                        json=stream_body,
                        headers={"Authorization": f"Bearer {adapter.api_key}"},
                    ) as resp:
                        async for line in resp.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                text = delta.get("content") or ""
                                if "usage" in chunk:
                                    prompt_tokens = chunk["usage"].get("prompt_tokens", prompt_tokens)
                                    completion_tokens = chunk["usage"].get("completion_tokens", completion_tokens)
                            except Exception:
                                continue

                            if text:
                                if not blocks_started:
                                    blocks_started = True
                                    yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': msg_id, 'type': 'message', 'role': 'assistant', 'model': unified.model, 'content': []}})}\n\n"
                                    block_index = 0
                                    yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': block_index, 'content_block': {'type': 'text', 'text': ''}})}\n\n"
                                    active_block_type = "text"
                                yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': block_index, 'delta': {'type': 'text_delta', 'text': text}})}\n\n"

                        if blocks_started:
                            close = _close_block()
                            if close:
                                yield close
                            yield f"event: message_delta\ndata: {json.dumps({'type': 'message_delta', 'delta': {'stop_reason': finish_reason or 'end_turn'}})}\n\n"
                            yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"

                    t_end = time.time()
                    latency_ms = int((t_end - t_start) * 1000)
                    if prompt_tokens or completion_tokens:
                        cost, bill_cost = await calculate_cost(model, prompt_tokens, completion_tokens)
                    else:
                        cost, bill_cost = 0, 0
                    await record_success(adapter.provider_name)
                    log_entry = {
                        "request_id": request_id, "user_id": user_id,
                        "api_key_prefix": key_prefix, "model": model,
                        "provider": adapter.provider_name,
                        "prompt_tokens": str(prompt_tokens),
                        "completion_tokens": str(completion_tokens),
                        "cost": str(cost), "bill_cost": str(bill_cost),
                        "latency_ms": str(latency_ms),
                        "status": "success", "error_msg": "",
                        "ip": client_ip,
                    }
                    await redis.xadd("usage_log_stream", log_entry)
                except Exception as e:
                    stream_error = str(e)
                    try:
                        t_end = time.time()
                        latency_ms = int((t_end - t_start) * 1000)
                        await record_failure(adapter.provider_name, cb_config)
                        log_entry = {
                            "request_id": request_id, "user_id": user_id,
                            "api_key_prefix": key_prefix, "model": model,
                            "provider": adapter.provider_name,
                            "prompt_tokens": "0", "completion_tokens": "0",
                            "cost": "0", "bill_cost": "0",
                            "latency_ms": str(latency_ms),
                            "status": "error", "error_msg": stream_error,
                            "ip": client_ip,
                        }
                        await redis.xadd("usage_log_stream", log_entry)
                    except Exception:
                        pass
                finally:
                    await fallback_client.aclose()

            except Exception as e:
                stream_error = str(e)
                try:
                    t_end = time.time()
                    latency_ms = int((t_end - t_start) * 1000)
                    await record_failure(adapter.provider_name, cb_config)
                    log_entry = {
                        "request_id": request_id, "user_id": user_id,
                        "api_key_prefix": key_prefix, "model": model,
                        "provider": adapter.provider_name,
                        "prompt_tokens": "0", "completion_tokens": "0",
                        "cost": "0", "bill_cost": "0",
                        "latency_ms": str(latency_ms),
                        "status": "error", "error_msg": stream_error,
                        "ip": client_ip,
                    }
                    await redis.xadd("usage_log_stream", log_entry)
                except Exception:
                    pass

        return StreamingResponse(
            stream_anthropic(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # 8. Non-streaming: Call provider
    print(f"[DEBUG] anthropic_messages: NON-STREAMING path for {request_id}")
    t_start = time.time()
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = await asyncio.wait_for(
                adapter.chat_completion(unified),
                timeout=UPSTREAM_TIMEOUT,
            )
            latency_ms = int((time.time() - t_start) * 1000)
            await record_success(adapter.provider_name)

            if response.usage:
                cost, bill_cost = await calculate_cost(
                    model, response.usage.prompt_tokens, response.usage.completion_tokens,
                )
            else:
                cost, bill_cost = 0, 0

            # Write usage log
            log_entry = {
                "request_id": request_id,
                "user_id": user_id,
                "api_key_prefix": key_prefix,
                "model": model,
                "provider": adapter.provider_name,
                "prompt_tokens": str(response.usage.prompt_tokens) if response.usage else "0",
                "completion_tokens": str(response.usage.completion_tokens) if response.usage else "0",
                "cost": str(cost),
                "bill_cost": str(bill_cost),
                "latency_ms": str(latency_ms),
                "status": "success",
                "error_msg": "",
                "ip": client_ip,
            }
            await redis.xadd("usage_log_stream", log_entry)

            # Convert to Anthropic response format
            text = response.choices[0].message.content if response.choices else ""
            return {
                "id": f"msg_{request_id}",
                "type": "message",
                "role": "assistant",
                "model": model,
                "content": [{"type": "text", "text": text}],
                "stop_reason": response.choices[0].finish_reason if response.choices else "end_turn",
                "stop_sequence": None,
                "usage": {
                    "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "output_tokens": response.usage.completion_tokens if response.usage else 0,
                },
            }

        except asyncio.TimeoutError:
            last_error = "timeout"
        except Exception as e:
            last_error = str(e)
            if hasattr(e, 'response') and e.response is not None:
                status = getattr(e.response, 'status_code', 0)
                if 400 <= status < 500:
                    break
        if attempt < MAX_RETRIES:
            jitter = random.uniform(0.5, 1.5)
            await asyncio.sleep(RETRY_BACKOFF_BASE * (2 ** attempt) * jitter)

    # Error response
    latency_ms = int((time.time() - t_start) * 1000)
    await record_failure(adapter.provider_name, cb_config)

    log_entry = {
        "request_id": request_id,
        "user_id": user_id,
        "api_key_prefix": key_prefix,
        "model": model,
        "provider": adapter.provider_name,
        "prompt_tokens": "0",
        "completion_tokens": "0",
        "cost": "0",
        "bill_cost": "0",
        "latency_ms": str(latency_ms),
        "status": "error",
        "error_msg": last_error or "unknown",
        "ip": client_ip,
    }
    await redis.xadd("usage_log_stream", log_entry)
    raise HTTPException(status_code=503, detail={"error": "upstream_error"})


# ── OpenAI-compatible endpoint ──

@router.post("/chat/completions")
async def chat_completions(request: Request):
    # 1. Auth
    auth_info = await verify_api_key(request)
    user_id = auth_info["user_id"]
    rate_limit = auth_info["rate_limit"]
    key_prefix = auth_info.get("key_prefix", "")

    # 2. Rate limit
    await check_rate_limit(user_id, rate_limit)
    client_ip = request.client.host if request.client else "unknown"

    # 3. Parse request
    body = await request.json()
    unified = UnifiedRequest(**body)
    request_id = f"req_{uuid.uuid4().hex[:16]}"

    # 4. Check model allowlist
    auth_allowlist = auth_info.get("model_allowlist", "")
    if auth_allowlist:
        allowed = [m.strip() for m in auth_allowlist.split(",") if m.strip()]
        if allowed and unified.model not in allowed:
            raise HTTPException(status_code=403, detail={"error": "model_not_allowed"})

    # 5. Find adapter
    adapter = find_adapter(unified.model, _adapters)
    if adapter is None:
        raise HTTPException(status_code=400, detail={"error": "invalid_model"})

    # 5. Circuit breaker check
    cb_config = CIRCUIT_BREAKER_CONFIG.get(
        adapter.provider_name,
        {"failure_threshold": 3, "timeout_seconds": 30, "half_open_ttl": 30},
    )
    if not await should_attempt(adapter.provider_name, cb_config):
        raise HTTPException(status_code=503, detail={"error": "model_temporarily_unavailable"})

    # 5.5. Balance + plan check
    user_balance = auth_info.get("balance", 0)
    has_plans = auth_info.get("has_plans", False)
    if user_balance <= 0 and not has_plans:
        raise HTTPException(status_code=402, detail={"error": "insufficient_balance"})

    # 6. Streaming path
    is_stream = body.get("stream", False)
    if is_stream:
        from fastapi.responses import StreamingResponse

        async def stream_openai():
            prompt_tokens = 0
            completion_tokens = 0
            finish_reason = None
            msg_id = "chatcmpl-" + uuid.uuid4().hex[:12]
            created = int(time.time())
            try:
                async for text, fr, usage in adapter.stream_completion(unified):
                    if text:
                        chunk_data = json.dumps({"id": msg_id, "object": "chat.completion.chunk", "created": created, "model": unified.model, "choices": [{"delta": {"content": text}, "index": 0}]})
                        yield "data: " + chunk_data + "\n\n"
                    if fr:
                        finish_reason = fr
                    if usage:
                        prompt_tokens = usage.get("prompt_tokens", 0)
                        completion_tokens = usage.get("completion_tokens", 0)
                final_chunk = json.dumps({"id": msg_id, "object": "chat.completion.chunk", "created": created, "model": unified.model, "choices": [{"delta": {}, "index": 0, "finish_reason": finish_reason or "stop"}]})
                yield "data: " + final_chunk + "\n\n"
                yield "data: [DONE]\n\n"
                t_end = time.time()
                latency_ms = int((t_end - t_start) * 1000)
                if prompt_tokens or completion_tokens:
                    cost, bill_cost = await calculate_cost(unified.model, prompt_tokens, completion_tokens)
                else:
                    cost, bill_cost = 0, 0
                await record_success(adapter.provider_name)
                await redis.xadd("usage_log_stream", {
                    "request_id": request_id, "user_id": user_id,
                    "api_key_prefix": key_prefix, "model": unified.model,
                    "provider": adapter.provider_name,
                    "prompt_tokens": str(prompt_tokens),
                    "completion_tokens": str(completion_tokens),
                    "cost": str(cost), "bill_cost": str(bill_cost),
                    "latency_ms": str(latency_ms),
                    "status": "success", "error_msg": "", "ip": client_ip,
                })
            except Exception as e:
                try:
                    t_end = time.time()
                    latency_ms = int((t_end - t_start) * 1000)
                    await record_failure(adapter.provider_name, cb_config)
                    await redis.xadd("usage_log_stream", {
                        "request_id": request_id, "user_id": user_id,
                        "api_key_prefix": key_prefix, "model": unified.model,
                        "provider": adapter.provider_name,
                        "prompt_tokens": "0", "completion_tokens": "0",
                        "cost": "0", "bill_cost": "0",
                        "latency_ms": str(latency_ms),
                        "status": "error", "error_msg": str(e), "ip": client_ip,
                    })
                except Exception:
                    pass

        return StreamingResponse(
            stream_openai(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    # 7. Non-streaming: Call provider with retries
    t_start = time.time()
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = await asyncio.wait_for(
                adapter.chat_completion(unified),
                timeout=UPSTREAM_TIMEOUT,
            )
            latency_ms = int((time.time() - t_start) * 1000)

            await record_success(adapter.provider_name)

            if response.usage:
                cost, bill_cost = await calculate_cost(
                    unified.model,
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                )
                response.usage.total_tokens = response.usage.prompt_tokens + response.usage.completion_tokens
            else:
                cost, bill_cost = 0, 0

            # 7. Write usage log to Redis Stream
            log_entry = {
                "request_id": request_id,
                "user_id": user_id,
                "api_key_prefix": key_prefix,
                "model": unified.model,
                "provider": adapter.provider_name,
                "prompt_tokens": str(response.usage.prompt_tokens) if response.usage else "0",
                "completion_tokens": str(response.usage.completion_tokens) if response.usage else "0",
                "cost": str(cost),
                "bill_cost": str(bill_cost),
                "latency_ms": str(latency_ms),
                "status": "success",
                "error_msg": "",
                "ip": client_ip,
            }
            await redis.xadd("usage_log_stream", log_entry)

            return response.model_dump()

        except asyncio.TimeoutError:
            last_error = "timeout"
        except Exception as e:
            last_error = str(e)
            # Don't retry 4xx errors (client errors)
            if hasattr(e, 'response') and e.response is not None:
                status = getattr(e.response, 'status_code', 0)
                if 400 <= status < 500:
                    break

        if attempt < MAX_RETRIES:
            jitter = random.uniform(0.5, 1.5)
            await asyncio.sleep(RETRY_BACKOFF_BASE * (2 ** attempt) * jitter)

    # All retries failed
    latency_ms = int((time.time() - t_start) * 1000)
    await record_failure(adapter.provider_name, cb_config)

    log_entry = {
        "request_id": request_id,
        "user_id": user_id,
        "api_key_prefix": key_prefix,
        "model": unified.model,
        "provider": adapter.provider_name,
        "prompt_tokens": "0",
        "completion_tokens": "0",
        "cost": "0",
        "bill_cost": "0",
        "latency_ms": str(latency_ms),
        "status": "error",
        "error_msg": last_error or "unknown",
        "ip": client_ip,
    }
    await redis.xadd("usage_log_stream", log_entry)

    raise HTTPException(status_code=503, detail={"error": "upstream_error"})


@router.get("/models")
async def list_models():
    models = []
    seen = set()
    for adapter in _adapters:
        for pattern in adapter.model_patterns:
            if pattern.endswith("-"):
                for m in _KNOWN_MODELS.get(adapter.provider_name, []):
                    if m not in seen:
                        seen.add(m)
                        models.append({"id": m, "object": "model", "provider": adapter.provider_name})
            else:
                if pattern not in seen:
                    seen.add(pattern)
                    models.append({"id": pattern, "object": "model", "provider": adapter.provider_name})
    return {"object": "list", "data": models}

_KNOWN_MODELS = {
    "deepseek": ["deepseek-v4-flash", "deepseek-v4-pro"],
}
