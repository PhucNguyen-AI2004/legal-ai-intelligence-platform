#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  printf 'Usage: %s [backup-directory]\n' "${0##*/}" >&2
}

backup_root="${1:-backups}"
if [[ $# -gt 1 || "$backup_root" == "/" || -z "$backup_root" ]]; then
  usage
  exit 64
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output_dir="${backup_root%/}/$timestamp"
mkdir -p "$output_dir"

compose=(docker compose --env-file .env.production -f docker-compose.prod.yml)

# Expansion is intentionally deferred to sh inside the PostgreSQL container.
# shellcheck disable=SC2016
"${compose[@]}" exec -T postgres sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' >"$output_dir/postgres.dump"

"${compose[@]}" run --rm --no-deps --entrypoint sh backend -c 'tar -C /app/storage -czf - documents' >"$output_dir/documents.tar.gz"

sha256sum "$output_dir/postgres.dump" "$output_dir/documents.tar.gz" >"$output_dir/SHA256SUMS"

printf 'Backup created at %s\n' "$output_dir"