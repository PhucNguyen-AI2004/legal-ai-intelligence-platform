#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  printf 'Usage: %s [environment-file]\n' "${0##*/}" >&2
}

env_file="${1:-.env.production}"
if [[ $# -gt 1 ]]; then
  usage
  exit 64
fi
if [[ ! -f "$env_file" ]]; then
  printf 'Production environment file not found: %s\n' "$env_file" >&2
  exit 66
fi

required=(APP_ENV FRONTEND_ORIGIN SITE_ADDRESS POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD DATABASE_URL SECRET_KEY LLM_MODEL LLM_API_KEY)
for name in "${required[@]}"; do
  if ! grep -Eq "^${name}=.+" "$env_file"; then
    printf 'Missing required production variable: %s\n' "$name" >&2
    exit 78
  fi
done

if grep -Eq '(^|=)(CHANGE_ME|local_dev_only_change_me)' "$env_file"; then
  printf 'Production environment still contains a documented placeholder.\n' >&2
  exit 78
fi
if ! grep -Eq '^APP_ENV=production$' "$env_file"; then
  printf 'APP_ENV must be production.\n' >&2
  exit 78
fi

printf 'Production environment contract passed structural validation (values not printed).\n'
