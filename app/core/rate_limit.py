import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, Response

from app.api.dependencies import CurrentUser
from app.core.config import Settings, get_settings
from app.core.redis import get_redis_client


logger = logging.getLogger("app.rate_limit")

_FIXED_WINDOW_SCRIPT = """
local now = redis.call('TIME')
local window = tonumber(ARGV[3])
local bucket = math.floor(tonumber(now[1]) / window)
local window_ttl = window - (tonumber(now[1]) % window)
local key = ARGV[1] .. ':' .. bucket
local current = redis.call('INCR', key)
if current == 1 then
  redis.call('EXPIRE', key, window_ttl)
end
local ttl = redis.call('TTL', key)
if ttl < 0 then
  redis.call('EXPIRE', key, window_ttl)
  ttl = window_ttl
end
return {current, ttl}
"""


class RateLimitPolicy(StrEnum):
    AUTH = "auth"
    AI = "ai"
    DOCUMENT_WRITE = "document_write"


class RateLimitBackendError(Exception):
    pass


@dataclass(frozen=True)
class RateLimitResult:
    limit: int
    remaining: int
    retry_after: int
    allowed: bool


class RedisRateLimiter:
    def __init__(self, client: Any, settings: Settings):
        self.client = client
        self.settings = settings

    async def check(self, policy: RateLimitPolicy, identity_type: str, identity: str) -> RateLimitResult:
        limit = self._limit(policy)
        prefix = f"legalai:ratelimit:{policy.value}:{identity_type}:{identity}"
        try:
            raw = await self.client.eval(
                _FIXED_WINDOW_SCRIPT,
                0,
                prefix,
                limit,
                self.settings.rate_limit_window_seconds,
            )
            if not isinstance(raw, (list, tuple)) or len(raw) != 2:
                raise ValueError("invalid rate-limit result")
            current, ttl = int(raw[0]), int(raw[1])
            if current < 1 or ttl < 0:
                raise ValueError("invalid rate-limit values")
        except Exception as exc:
            raise RateLimitBackendError from exc
        return RateLimitResult(
            limit=limit,
            remaining=max(0, limit - current),
            retry_after=max(1, ttl),
            allowed=current <= limit,
        )

    def _limit(self, policy: RateLimitPolicy) -> int:
        return {
            RateLimitPolicy.AUTH: self.settings.auth_rate_limit,
            RateLimitPolicy.AI: self.settings.ai_rate_limit,
            RateLimitPolicy.DOCUMENT_WRITE: self.settings.document_write_rate_limit,
        }[policy]


def get_rate_limiter(
    client: Annotated[Any, Depends(get_redis_client)],
) -> RedisRateLimiter:
    return RedisRateLimiter(client, get_settings())


def _apply_result(
    result: RateLimitResult,
    response: Response,
    request: Request,
    policy: RateLimitPolicy,
) -> RateLimitResult:
    headers = {
        "X-RateLimit-Limit": str(result.limit),
        "X-RateLimit-Remaining": str(result.remaining),
    }
    if result.allowed:
        response.headers.update(headers)
        return result
    headers["Retry-After"] = str(result.retry_after)
    logger.warning(
        "Rate limit exceeded",
        extra={
            "event": "rate_limit_exceeded",
            "policy": policy.value,
            "path": request.url.path,
            "status_code": 429,
            "retry_after": result.retry_after,
        },
    )
    raise HTTPException(429, "Rate limit exceeded", headers=headers)


async def _enforce(
    policy: RateLimitPolicy,
    identity_type: str,
    identity: str,
    request: Request,
    response: Response,
    limiter: RedisRateLimiter,
) -> RateLimitResult:
    try:
        result = await limiter.check(policy, identity_type, identity)
    except RateLimitBackendError:
        logger.error(
            "Rate-limit backend unavailable",
            extra={
                "event": "rate_limit_backend_unavailable",
                "policy": policy.value,
                "path": request.url.path,
                "status_code": 503,
            },
        )
        raise HTTPException(503, "Rate limiting service unavailable") from None
    return _apply_result(result, response, request, policy)


async def enforce_auth_rate_limit(
    request: Request,
    response: Response,
    limiter: Annotated[RedisRateLimiter, Depends(get_rate_limiter)],
) -> RateLimitResult:
    # Do not trust forwarding headers until Phase 10 defines trusted proxies.
    peer = request.client.host if request.client is not None else "unknown"
    return await _enforce(RateLimitPolicy.AUTH, "ip", peer, request, response, limiter)


async def enforce_ai_rate_limit(
    user: CurrentUser,
    request: Request,
    response: Response,
    limiter: Annotated[RedisRateLimiter, Depends(get_rate_limiter)],
) -> RateLimitResult:
    return await _enforce(RateLimitPolicy.AI, "user", str(user.id), request, response, limiter)


async def enforce_document_write_rate_limit(
    user: CurrentUser,
    request: Request,
    response: Response,
    limiter: Annotated[RedisRateLimiter, Depends(get_rate_limiter)],
) -> RateLimitResult:
    return await _enforce(
        RateLimitPolicy.DOCUMENT_WRITE, "user", str(user.id), request, response, limiter
    )


AuthRateLimit = Annotated[RateLimitResult, Depends(enforce_auth_rate_limit)]
AiRateLimit = Annotated[RateLimitResult, Depends(enforce_ai_rate_limit)]
DocumentWriteRateLimit = Annotated[RateLimitResult, Depends(enforce_document_write_rate_limit)]
