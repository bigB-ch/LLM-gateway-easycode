from abc import ABC, abstractmethod
import httpx
from schemas import UnifiedRequest, UnifiedResponse


class BaseAdapter(ABC):
    model_patterns: list[str] = []
    provider_name: str = ""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    @abstractmethod
    async def chat_completion(self, request: UnifiedRequest) -> UnifiedResponse:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...

    async def get_balance(self) -> dict | None:
        """Return {'balance': float, 'currency': str} or None if not supported."""
        return None

    def matches(self, model: str) -> bool:
        return any(model.startswith(p) for p in self.model_patterns)
