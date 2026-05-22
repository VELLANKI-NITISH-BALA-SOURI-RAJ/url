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
            if key in self.data:
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

    async def delete(self, key: str):
        if key in self.data:
            del self.data[key]
        if key in self.expiry:
            del self.expiry[key]

class CacheService:
    def __init__(self):
        if settings.REDIS_URL == "memory" or "<REDIS_HOST>" in settings.REDIS_URL or not settings.REDIS_URL:
            self.redis = SimpleMemoryCache()
            self.is_redis = False
        else:
            self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.is_redis = True
            self.fallback_cache = SimpleMemoryCache()

    async def get_url(self, code: str) -> str:
        if not self.is_redis:
            return await self.redis.get(f"url:{code}")
        try:
            return await self.redis.get(f"url:{code}")
        except Exception as e:
            print(f"Warning: Redis get_url failed, falling back to memory: {e}")
            return await self.fallback_cache.get(f"url:{code}")

    async def set_url(self, code: str, url: str):
        if not self.is_redis:
            await self.redis.setex(f"url:{code}", 86400, url)
            return
        try:
            await self.redis.setex(f"url:{code}", 86400, url)
        except Exception as e:
            print(f"Warning: Redis set_url failed, falling back to memory: {e}")
            await self.fallback_cache.setex(f"url:{code}", 86400, url)

    async def delete_url(self, code: str):
        if not self.is_redis:
            await self.redis.delete(f"url:{code}")
            return
        try:
            await self.redis.delete(f"url:{code}")
        except Exception as e:
            print(f"Warning: Redis delete_url failed, falling back to memory: {e}")
            await self.fallback_cache.delete(f"url:{code}")

    async def increment_rate_limit(self, ip: str) -> int:
        key = f"ratelimit:{ip}"
        if not self.is_redis:
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, 60)
            return count
        try:
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, 60)
            return count
        except Exception as e:
            print(f"Warning: Redis rate limit failed, falling back to memory: {e}")
            count = await self.fallback_cache.incr(key)
            if count == 1:
                await self.fallback_cache.expire(key, 60)
            return count

cache_service = CacheService()
