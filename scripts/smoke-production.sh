#!/usr/bin/env bash
set -Eeuo pipefail

base_url="${1:-http://localhost}"
base_url="${base_url%/}"

curl --fail --silent --show-error "$base_url/api/health" >/dev/null
curl --fail --silent --show-error "$base_url/api/ready" >/dev/null
curl --fail --silent --show-error "$base_url/" >/dev/null
printf 'Production proxy smoke checks passed for %s\n' "$base_url"
