# Operations

In Bash, set `COMPOSE="docker compose --env-file .env.production -f docker-compose.prod.yml"` or repeat the full command.

- Status: `$COMPOSE ps`
- Logs: `$COMPOSE logs --tail 200 backend` (replace service with worker, frontend, reverse-proxy, postgres, or redis)
- Health/readiness: `curl -fsS "$SITE_ADDRESS/api/health"` and `curl -fsS "$SITE_ADDRESS/api/ready"`
- Queue: `$COMPOSE exec redis redis-cli LLEN rq:queue:documents`
- Worker: `$COMPOSE exec worker rq info -u redis://redis:6379/0`
- Disk: `docker system df` plus host filesystem tools; do not prune volumes as routine maintenance.
- Restart one service: `$COMPOSE restart backend`
- Refresh stack: build validated production images separately, then run `$COMPOSE up -d` after the required migration. Avoid parallel full-stack rebuilds and check host free disk space before image builds.
- Migration: `$COMPOSE --profile tools run --rm migrate`
- Backup: `bash scripts/backup-production.sh backups`
- Smoke: `bash scripts/smoke-production.sh "$SITE_ADDRESS"`

Containers log to stdout/stderr. Configure Docker daemon log rotation on the host; do not create unbounded container log files. `/ready` checks PostgreSQL and Redis, not worker heartbeat. RQ/AOF is not exactly-once; catastrophic accepted-job loss may require operator review.

Public host ports should be 80/443 only, plus operator-controlled SSH if needed. Internal networking does not replace host patching, firewall policy, secret rotation, least-privilege access, and backup testing.

The worker has no published port and no Docker HTTP healthcheck. This is intentional: it is an RQ process, not a web server. Validate it with `rq info` and a stop/queue/start recovery test; backend `/ready` does not claim worker readiness. Its `app` network attachment permits outbound model retrieval for an initially empty cache; it does not expose a listener publicly. PostgreSQL and Redis remain confined to the internal `data` network. Keep `POSTGRES_PASSWORD` raw for the database container and percent-encode reserved password characters separately in `DATABASE_URL`.
