"""OpenAI-compatible adapters: DeepSeek, Qwen, etc."""
import httpx
from adapters.openai import OpenAIAdapter


class DeepSeekAdapter(OpenAIAdapter):
    model_patterns = ["deepseek-"]
    provider_name = "deepseek"

    async def get_balance(self) -> dict | None:
        try:
            client = await self.get_client()
            resp = await client.get(
                f"{self.base_url}/user/balance",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                balance_info = data.get("balance_infos", [{}])
                total = sum(
                    float(b.get("total_balance", 0))
                    for b in balance_info
                )
                return {"balance": total, "currency": balance_info[0].get("currency", "CNY") if balance_info else "CNY"}
        except Exception:
            pass
        return None


class QwenAdapter(OpenAIAdapter):
    model_patterns = ["qwen-"]
    provider_name = "qwen"

    async def get_balance(self) -> dict | None:
        """Query DashScope billing for Qwen models."""
        try:
            client = await self.get_client()
            resp = await client.get(
                f"{self.base_url}/api/v1/usage/query_balance",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                total = float(data.get("data", {}).get("total_balance", 0))
                return {"balance": total, "currency": "CNY"}
        except Exception:
            pass
        return None
