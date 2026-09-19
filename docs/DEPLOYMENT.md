# Deployment

Phase 10 targets a provider-neutral Linux VPS/VM with Docker Engine and Compose. No external deployment or image publication is automatic.

## Production order

1. Copy `.env.production.example` to `.env.production` and replace every placeholder privately.
2. Set `SITE_ADDRESS` and `FRONTEND_ORIGIN` to the same public HTTPS origin when a real domain exists. For local simulation, keep `http://localhost`.
   Set `DATABASE_URL` explicitly for the application. If its password contains URI-reserved characters such as `@`, `:`, `/`, `#`, or `%`, percent-encode those characters in the URL password component. `POSTGRES_PASSWORD` remains the raw value supplied to the PostgreSQL container.
3. Run `bash scripts/validate-production-config.sh .env.production`.
4. Build: `docker compose --env-file .env.production -f docker-compose.prod.yml build`.
5. Start dependencies: `docker compose --env-file .env.production -f docker-compose.prod.yml up -d postgres redis`.
6. Migrate once: `docker compose --env-file .env.production -f docker-compose.prod.yml --profile tools run --rm migrate`.
7. Start services: `docker compose --env-file .env.production -f docker-compose.prod.yml up -d backend worker frontend reverse-proxy`.
8. Run `bash scripts/smoke-production.sh "$SITE_ADDRESS"` and the owner smoke matrix in `PHASE_10_VALIDATION.md`.

Migration failure stops deployment. Do not start new application containers until corrected. Never run automatic startup migrations or blindly downgrade.

## TLS, routing, and host preparation

Caddy obtains HTTPS certificates when `SITE_ADDRESS` is a real domain. The owner must create DNS A/AAAA records and allow inbound TCP 80/443 (plus UDP 443 if HTTP/3 is desired). Do not enable HSTS until HTTPS is verified. Firewall and DNS changes are operator actions.

The frontend is built with `/api`; Caddy strips that prefix before forwarding to FastAPI. The backend is configured with `ROOT_PATH=/api`, so generated URLs such as Swagger's OpenAPI request retain the public prefix while application route declarations remain unprefixed. Production CORS remains the explicit `FRONTEND_ORIGIN`. The proxy accepts 25 MB bodies so multipart overhead does not undercut the unchanged 20 MiB application file limit.

The worker joins both existing networks: `data` for PostgreSQL/Redis and `app` for outbound-capable connectivity when an empty model cache must fetch the configured embedding model. It publishes no port, so this attachment does not make the worker publicly reachable. Its inherited image HTTP healthcheck is explicitly disabled because an RQ worker does not serve port 8000; use `rq info` and queue/job recovery checks for operational validation. PostgreSQL and Redis remain only on the internal `data` network.

## Rollback

Record the previous commit/image tags and back up before risky migrations. If the schema is backward-compatible, restore the prior application version and recreate only application containers. Otherwise stop writes, assess migration-specific recovery, and restore a tested database/document backup if necessary. Redis AOF is not the authoritative rollback source.
