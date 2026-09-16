import logging
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import Response
from starlette.requests import Request

from app.api import documents as documents_api
from app.api import health as health_api
from app.api import rag as rag_api
from app.core.config import get_settings
from app.core.rate_limit import (
    RateLimitBackendError,
    RateLimitPolicy,
    RateLimitResult,
    RedisRateLimiter,
    enforce_auth_rate_limit,
    get_rate_limiter,
)
from app.main import app


class ScriptedRedis:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    async def eval(self, *args):
        self.calls.append(args)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class CountingLimiter:
    def __init__(self, limits=None, unavailable=False):
        self.limits = limits or {
            RateLimitPolicy.AUTH: 10,
            RateLimitPolicy.AI: 1,
            RateLimitPolicy.DOCUMENT_WRITE: 1,
        }
        self.unavailable = unavailable
        self.counts = {}
        self.identities = []

    async def check(self, policy, identity_type, identity):
        if self.unavailable:
            raise RateLimitBackendError
        key = (policy, identity_type, identity)
        self.identities.append(key)
        current = self.counts.get(key, 0) + 1
        self.counts[key] = current
        limit = self.limits[policy]
        return RateLimitResult(limit, max(0, limit - current), 37, current <= limit)


@pytest.mark.anyio
async def test_atomic_store_counter_remaining_limit_and_ttl(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "auth_rate_limit", 2)
    redis = ScriptedRedis([[1, 55], [2, 54], [3, 53]])
    limiter = RedisRateLimiter(redis, settings)

    first = await limiter.check(RateLimitPolicy.AUTH, "ip", "127.0.0.1")
    second = await limiter.check(RateLimitPolicy.AUTH, "ip", "127.0.0.1")
    exceeded = await limiter.check(RateLimitPolicy.AUTH, "ip", "127.0.0.1")

    assert (first.allowed, first.remaining) == (True, 1)
    assert (second.allowed, second.remaining) == (True, 0)
    assert (exceeded.allowed, exceeded.remaining, exceeded.retry_after) == (False, 0, 53)
    assert all(call[0].find("TIME") >= 0 and call[2].startswith("legalai:ratelimit:auth:ip:") for call in redis.calls)
    assert all(call[4] == settings.rate_limit_window_seconds for call in redis.calls)


@pytest.mark.anyio
@pytest.mark.parametrize("result", [None, [1], [0, 50], [1, -1], RuntimeError("redis secret")])
async def test_invalid_or_unavailable_redis_result_fails_closed(result):
    limiter = RedisRateLimiter(ScriptedRedis([result]), get_settings())
    with pytest.raises(RateLimitBackendError):
        await limiter.check(RateLimitPolicy.AI, "user", str(uuid4()))


@pytest.mark.anyio
async def test_users_and_policies_have_independent_buckets():
    limiter = CountingLimiter()
    user_a, user_b = str(uuid4()), str(uuid4())
    assert (await limiter.check(RateLimitPolicy.AI, "user", user_a)).allowed
    assert not (await limiter.check(RateLimitPolicy.AI, "user", user_a)).allowed
    assert (await limiter.check(RateLimitPolicy.AI, "user", user_b)).allowed
    assert (await limiter.check(RateLimitPolicy.DOCUMENT_WRITE, "user", user_a)).allowed


@pytest.mark.anyio
async def test_auth_uses_peer_ip_and_ignores_forwarded_header():
    limiter = CountingLimiter()
    request = Request({
        "type": "http",
        "method": "POST",
        "path": "/auth/login",
        "headers": [(b"x-forwarded-for", b"203.0.113.10")],
        "client": ("192.0.2.20", 1234),
        "scheme": "http",
        "server": ("test", 80),
        "query_string": b"",
    })
    await enforce_auth_rate_limit(request, Response(), limiter)
    assert limiter.identities == [(RateLimitPolicy.AUTH, "ip", "192.0.2.20")]


@pytest.fixture
def limited(client):
    limiter = CountingLimiter()
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    yield limiter
    app.dependency_overrides.pop(get_rate_limiter, None)


def _account(client, email):
    password = "SyntheticPassword123!"
    assert client.post("/auth/register", json={
        "email": email, "password": password, "full_name": "Synthetic User"
    }).status_code == 201
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": "Bearer " + login.json()["access_token"]}


def test_login_limit_precedes_authentication_and_has_safe_headers(client, monkeypatch):
    limiter = CountingLimiter(limits={
        RateLimitPolicy.AUTH: 2,
        RateLimitPolicy.AI: 1,
        RateLimitPolicy.DOCUMENT_WRITE: 1,
    })
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    calls = []
    monkeypatch.setattr(rag_api, "logger", logging.getLogger("app.rate_limit"), raising=False)
    from app.api import auth as auth_api
    monkeypatch.setattr(auth_api, "authenticate_user", lambda *args: calls.append(args))
    payload = {"email": "unknown@example.com", "password": "SyntheticWrong123!"}
    try:
        assert client.post("/auth/login", json=payload).status_code == 401
        assert client.post("/auth/login", json=payload).status_code == 401
        response = client.post("/auth/login", json=payload)
    finally:
        app.dependency_overrides.pop(get_rate_limiter, None)

    assert response.status_code == 429
    assert response.json() == {"detail": "Rate limit exceeded"}
    assert response.headers["Retry-After"] == "37"
    assert response.headers["X-RateLimit-Limit"] == "2"
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert response.headers["X-Request-ID"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert len(calls) == 2


def test_registration_limit_is_not_email_specific(client):
    limiter = CountingLimiter(limits={
        RateLimitPolicy.AUTH: 1,
        RateLimitPolicy.AI: 1,
        RateLimitPolicy.DOCUMENT_WRITE: 1,
    })
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    try:
        first = client.post("/auth/register", json={
            "email": "first@example.com", "password": "SyntheticPassword123!", "full_name": "First User"
        })
        second = client.post("/auth/register", json={
            "email": "different@example.com", "password": "SyntheticPassword123!", "full_name": "Second User"
        })
    finally:
        app.dependency_overrides.pop(get_rate_limiter, None)
    assert first.status_code == 201
    assert second.status_code == 429


def test_ai_user_isolation_and_rejection_precedes_rag_work(client, limited, monkeypatch):
    user_a = _account(client, "limit-a@example.com")
    user_b = _account(client, "limit-b@example.com")
    calls = []
    monkeypatch.setattr(rag_api, "ask_question", lambda *args: calls.append(args) or SimpleNamespace(
        answer="none", grounded=False, citations=[], model=None, retrieved_chunks=0, used_chunks=0
    ))

    assert client.post("/rag/ask", headers=user_a, json={"question": "synthetic"}).status_code == 200
    rejected = client.post("/rag/ask", headers=user_a, json={"question": "synthetic"})
    assert rejected.status_code == 429
    assert len(calls) == 1
    assert client.post("/rag/ask", headers=user_b, json={"question": "synthetic"}).status_code == 200


def test_conversation_and_document_expensive_work_rejected_early(client, limited, monkeypatch):
    headers = _account(client, "limit-expensive@example.com")
    assert client.post("/rag/ask", headers=headers, json={"question": "first"}).status_code in {200, 503}

    from app.api import conversations as conversations_api
    monkeypatch.setattr(conversations_api, "post_message", lambda *args: pytest.fail("chat work executed"))
    conversation = client.post("/conversations", headers=headers, json={}).json()
    chat = client.post(
        f"/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"content": "must be rejected"},
    )
    assert chat.status_code == 429

    limited.counts[(RateLimitPolicy.DOCUMENT_WRITE, "user", next(
        identity for policy, kind, identity in limited.identities if policy == RateLimitPolicy.AI
    ))] = 1
    monkeypatch.setattr(documents_api.document_processing, "process_document", lambda *args: pytest.fail("processing executed"))
    processing = client.post(f"/documents/{uuid4()}/process", headers=headers)
    assert processing.status_code == 429


def test_rate_limit_backend_unavailable_returns_correlated_503(client, caplog):
    limiter = CountingLimiter(unavailable=True)
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    rate_logger = logging.getLogger("app.rate_limit")
    rate_logger.disabled = False
    try:
        with caplog.at_level(logging.ERROR, logger="app.rate_limit"):
            response = client.post("/auth/login", json={"email": "nobody@example.com", "password": "SyntheticWrong123!"})
    finally:
        app.dependency_overrides.pop(get_rate_limiter, None)
    assert response.status_code == 503
    assert response.json() == {"detail": "Rate limiting service unavailable"}
    assert response.headers["X-Request-ID"]
    record = next(record for record in caplog.records if getattr(record, "event", None) == "rate_limit_backend_unavailable")
    assert record.policy == "auth" and record.path == "/auth/login"
    assert "redis" not in record.getMessage().lower()


def test_readiness_requires_redis_and_failure_is_generic(client, monkeypatch):
    monkeypatch.setattr(health_api, "check_database_readiness", lambda: None)
    internal = "redis://secret-host:6379/0"

    async def fail_ping():
        raise RuntimeError(internal)

    monkeypatch.setattr(client.app.state.redis, "ping", fail_ping)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
    assert internal not in response.text
    assert response.headers["X-Request-ID"]
