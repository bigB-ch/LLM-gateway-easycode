"""OpenAI-compatible adapters for all providers."""
import httpx
from adapters.openai import OpenAIAdapter
from adapters.balance_utils import try_balance_endpoints


class DeepSeekAdapter(OpenAIAdapter):
    model_patterns = ["deepseek-"]
    provider_name = "deepseek"

    async def get_balance(self) -> dict | None:
        try:
            client = await self.get_client()
            result = await try_balance_endpoints(client, self.api_key, self.base_url)
            if result:
                return result
            resp = await client.get(
                f"{self.base_url}/user/balance",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                balance_info = data.get("balance_infos", [{}])
                total = sum(float(b.get("total_balance", 0)) for b in balance_info)
                return {"balance": total, "currency": balance_info[0].get("currency", "CNY") if balance_info else "CNY"}
        except Exception:
            pass
        return None


class QwenAdapter(OpenAIAdapter):
    model_patterns = ["qwen-"]
    provider_name = "qwen"

    async def get_balance(self) -> dict | None:
        try:
            client = await self.get_client()
            result = await try_balance_endpoints(client, self.api_key, self.base_url)
            if result:
                return result
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


class _ProxyBalanceMixin:
    async def get_balance(self) -> dict | None:
        try:
            client = await self.get_client()
            return await try_balance_endpoints(client, self.api_key, self.base_url)
        except Exception:
            return None


class ZhipuAdapter(_ProxyBalanceMixin, OpenAIAdapter):
    model_patterns = ["glm-"]
    provider_name = "zhipu"


class MoonshotAdapter(_ProxyBalanceMixin, OpenAIAdapter):
    model_patterns = ["kimi-"]
    provider_name = "moonshot"


class DoubaoAdapter(_ProxyBalanceMixin, OpenAIAdapter):
    model_patterns = ["doubao-"]
    provider_name = "doubao"


class MinimaxAdapter(_ProxyBalanceMixin, OpenAIAdapter):
    model_patterns = ["minimax-", "abab-"]
    provider_name = "minimax"


class KlingAdapter(_ProxyBalanceMixin, OpenAIAdapter):
    model_patterns = ["kling-"]
    provider_name = "kling"
