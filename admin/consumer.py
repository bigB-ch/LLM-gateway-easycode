import asyncio
import json
import os
import logging
from sqlalchemy import text
from database import engine
import redis_client

logger = logging.getLogger("consumer")
STREAM_KEY = "usage_log_stream"
GROUP_NAME = "usage_consumers"
DLQ_KEY = "usage_log_dlq"
MAX_RETRIES = 3


async def ensure_group():
    r = redis_client.redis
    try:
        await r.xgroup_create(STREAM_KEY, GROUP_NAME, id="0", mkstream=True)
    except Exception:
        pass


async def batch_insert(messages: list[tuple[str, dict]]) -> list[str]:
    if not messages:
        return []

    values_clauses = []
    params = {}
    msg_ids = []
    for i, (msg_id, data) in enumerate(messages):
        msg_ids.append(msg_id)
        idx = i
        values_clauses.append(
            f"(:rid_{idx}, :uid_{idx}, :prefix_{idx}, :model_{idx}, :provider_{idx}, "
            f":pt_{idx}, :ct_{idx}, :cost_{idx}, :bcost_{idx}, :lat_{idx}, :status_{idx}, :err_{idx}) "
            f"ON CONFLICT (request_id) DO NOTHING"
        )
        params.update({
            f"rid_{idx}": data.get("request_id", ""),
            f"uid_{idx}": data.get("user_id", ""),
            f"prefix_{idx}": data.get("api_key_prefix", ""),
            f"model_{idx}": data.get("model", ""),
            f"provider_{idx}": data.get("provider", ""),
            f"pt_{idx}": int(data.get("prompt_tokens", 0)),
            f"ct_{idx}": int(data.get("completion_tokens", 0)),
            f"cost_{idx}": int(data.get("cost", 0)),
            f"bcost_{idx}": int(data.get("bill_cost", 0)),
            f"lat_{idx}": int(data.get("latency_ms", 0)),
            f"status_{idx}": data.get("status", "error"),
            f"err_{idx}": data.get("error_msg", ""),
        })

    sql = (
        "INSERT INTO usage_logs "
        "(request_id, user_id, api_key_prefix, model, provider, prompt_tokens, completion_tokens, cost, bill_cost, latency_ms, status, error_msg) "
        "VALUES " + ", ".join(values_clauses)
    )

    async with engine.begin() as conn:
        await conn.execute(text(sql), params)

    return msg_ids


async def run_consumer():
    await ensure_group()
    r = redis_client.redis
    consumer_name = f"admin-{os.getpid()}"

    while True:
        try:
            messages = await r.xreadgroup(
                GROUP_NAME, consumer_name, {STREAM_KEY: ">"},
                count=100, block=5000,
            )
            if messages:
                for stream_name, entries in messages:
                    parsed = [(eid, json.loads(data)) for eid, data in entries]
                    acked = await batch_insert(parsed)
                    for eid in acked:
                        await r.xack(STREAM_KEY, GROUP_NAME, eid)

                    for eid, data in parsed:
                        if eid not in acked:
                            retries = await r.hget(f"dlq_retry:{eid}", "count")
                            retries = int(retries or 0) + 1
                            if retries > MAX_RETRIES:
                                await r.xadd(DLQ_KEY, {**data, "retries": str(retries)})
                                await r.xack(STREAM_KEY, GROUP_NAME, eid)
                                await r.delete(f"dlq_retry:{eid}")
                            else:
                                await r.hset(f"dlq_retry:{eid}", "count", str(retries))

            pending_info = await r.xpending(STREAM_KEY, GROUP_NAME)
            if pending_info and pending_info.get("pending", 0) > 100:
                pending_msgs = await r.xpending_range(
                    STREAM_KEY, GROUP_NAME, min="-", max="+", count=50,
                )
                for entry in pending_msgs:
                    msg = await r.xrange(STREAM_KEY, entry["message_id"], entry["message_id"])
                    if msg:
                        eid, data = msg[0]
                        parsed = json.loads(data)
                        acked = await batch_insert([(eid, parsed)])
                        for eid2 in acked:
                            await r.xack(STREAM_KEY, GROUP_NAME, eid2)

        except Exception as e:
            logger.error(f"Consumer error: {e}")
            await asyncio.sleep(1)
