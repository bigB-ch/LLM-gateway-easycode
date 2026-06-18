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
            f":pt_{idx}, :ct_{idx}, :cost_{idx}, :bcost_{idx}, :lat_{idx}, :status_{idx}, :err_{idx}, :ip_{idx}, NOW()) "
            ""
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
            f"ip_{idx}": data.get("ip", ""),
        })

    sql = (
        "INSERT INTO usage_logs "
        "(request_id, user_id, api_key_prefix, model, provider, prompt_tokens, completion_tokens, cost, bill_cost, latency_ms, status, error_msg, ip, created_at) "
        "VALUES " + ", ".join(values_clauses) + " ON CONFLICT (request_id) DO NOTHING"
    )

    async with engine.begin() as conn:
        result = await conn.execute(text(sql), params)
        inserted = result.rowcount

        for i, (msg_id, data) in enumerate(messages):
            if data.get("status") != "success":
                continue
            user_id = data.get("user_id", "")
            bill_cost = int(data.get("bill_cost", 0))
            if not user_id or bill_cost <= 0:
                continue

            remaining = bill_cost

            # Deduct from plans first
            plan_result = await conn.execute(
                text(
                    "SELECT id, token_remaining FROM user_plans "
                    "WHERE user_id = :uid AND token_remaining > 0 AND expires_at > NOW() "
                    "ORDER BY expires_at ASC FOR UPDATE"
                ),
                {"uid": user_id},
            )
            for plan_row in plan_result:
                if remaining <= 0:
                    break
                plan_id = plan_row[0]
                plan_tokens = plan_row[1]
                deduct = min(remaining, plan_tokens)
                await conn.execute(
                    text("UPDATE user_plans SET token_remaining = token_remaining - :d WHERE id = :pid"),
                    {"d": deduct, "pid": plan_id},
                )
                remaining -= deduct

            if remaining > 0:
                try:
                    r = redis_client.redis
                    await r.set(f"user_has_plans:{user_id}", "0", ex=86400)
                except Exception:
                    pass

            if remaining > 0:
                user_result = await conn.execute(
                    text("SELECT balance FROM users WHERE id = :uid FOR UPDATE"),
                    {"uid": user_id},
                )
                user_row = user_result.fetchone()
                if user_row:
                    user_balance = user_row[0]
                    if user_balance < remaining:
                        remaining = user_balance
                    if remaining > 0:
                        await conn.execute(
                            text("UPDATE users SET balance = balance - :d WHERE id = :uid"),
                            {"d": remaining, "uid": user_id},
                        )
                        try:
                            new_balance = user_balance - remaining
                            r = redis_client.redis
                            await r.set(f"user_balance:{user_id}", str(new_balance), ex=3600)
                        except Exception:
                            pass

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
            if pending_info and pending_info.get("pending", 0) > 10:
                pending_msgs = await r.xpending_range(
                    STREAM_KEY, GROUP_NAME, min="-", max="+", count=50,
                )
                for entry in pending_msgs:
                    msg = await r.xrange(STREAM_KEY, entry["message_id"], entry["message_id"])
                    if msg:
                        eid, data = msg[0]
                        parsed = data
                        acked = await batch_insert([(eid, parsed)])
                        for eid2 in acked:
                            await r.xack(STREAM_KEY, GROUP_NAME, eid2)

        except Exception as e:
            logger.error(f"Consumer error: {e}")
            await asyncio.sleep(1)
