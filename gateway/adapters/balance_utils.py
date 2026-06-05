"""Shared balance-checking utilities for all adapters."""


async def try_balance_endpoints(client, api_key, base_url) -> dict | None:
    """Try common balance endpoints used by new-api/one-api proxy platforms.
    Strips /v1 suffix since balance/admin endpoints are not under /v1."""
    clean_base = base_url.rstrip("/")
    if clean_base.endswith("/v1"):
        clean_base = clean_base[:-3]

    endpoints = [
        ("/api/user/balance", _parse_newapi_balance),
        ("/user/balance", _parse_newapi_balance),
        ("/api/user/self", _parse_self_balance),
    ]
    for path, parser in endpoints:
        url = f"{clean_base}{path}"
        try:
            resp = await client.get(
                url, headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                result = parser(data)
                if result:
                    return result
        except Exception:
            continue
    return None


def _parse_newapi_balance(data: dict) -> dict | None:
    inner = data.get("data", data)
    if isinstance(inner, dict):
        for key in ("balance", "total_balance", "quota"):
            if key in inner and inner[key] is not None:
                return {"balance": float(inner[key]), "currency": inner.get("currency", "CNY")}
        # DeepSeek format: {"balance_infos": [{"total_balance": 100.0, "currency": "CNY"}]}
        if "balance_infos" in inner:
            infos = inner["balance_infos"]
            if isinstance(infos, list) and len(infos) > 0:
                total = sum(float(b.get("total_balance", 0)) for b in infos)
                currency = infos[0].get("currency", "CNY")
                return {"balance": total, "currency": currency}
    if "balance" in data:
        return {"balance": float(data["balance"]), "currency": "CNY"}
    return None


def _parse_self_balance(data: dict) -> dict | None:
    inner = data.get("data", data)
    if isinstance(inner, dict):
        for key in ("quota", "balance", "remain_quota", "remaining_quota"):
            if key in inner and inner[key] is not None:
                return {"balance": float(inner[key]), "currency": "CNY"}
    return None
