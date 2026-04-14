import redis.asyncio as redis
from app.core.config import settings
import json
import time

class SimpleMemoryCache:
    """Mock Redis behavior for local development without Docker."""
    def __init__(self):
        self.data = {}
        self.expiry = {}
        self.rate_limits = {}

    async def get(self, key: str) -> str:
        if key in self.expiry and self.expiry[key] < time.time():
            del self.data[key]
            del self.expiry[key]
            return None
        return self.data.get(key)

    async def setex(self, key: str, seconds: int, value: str):
        self.data[key] = value
        self.expiry[key] = time.time() + seconds

    async def incr(self, key: str) -> int:
        current = self.rate_limits.get(key, 0)
        self.rate_limits[key] = current + 1
        return self.rate_limits[key]

    async def expire(self, key: str, seconds: int):
        pass # Simplified for mock

class CacheService:
    def __init__(self):
        if settings.REDIS_URL == "memory":
            self.redis = SimpleMemoryCache()
        else:
            self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def get_url(self, code: str) -> str:
        return await self.redis.get(f"url:{code}")

    async def set_url(self, code: str, url: str):
        await self.redis.setex(f"url:{code}", 86400, url)

    async def increment_rate_limit(self, ip: str) -> int:
        key = f"ratelimit:{ip}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 60)
        return count

cache_service = CacheService()
