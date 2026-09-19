# Backup and restore

`scripts/backup-production.sh` creates a timestamped PostgreSQL custom dump, document archive, and SHA-256 manifest under ignored `backups/`. It does not schedule itself, include Redis, or print secrets. Model cache is rebuildable. Redis AOF improves queue restart durability but is not an authoritative business backup.

## Backup

Run `bash scripts/backup-production.sh backups`, verify non-zero files, then run `sha256sum -c backups/<timestamp>/SHA256SUMS`. Store the directory encrypted outside the host. Backups contain private legal data and password hashes.

## Restore (operator action)

Test outside production first. Verify checksums, confirm the target, stop backend and worker to prevent writes, and take a fresh backup before replacing data. Restore PostgreSQL with `pg_restore` into the explicitly selected database and restore `documents.tar.gz` into the existing document-storage volume with ownership compatible with the non-root application user. Start services, run health/readiness, then verify authentication, documents, search, chat/citations, and queue behavior.

Restore commands are intentionally not automated because they replace authoritative state. Never restore during startup, delete volumes as a shortcut, or treat Redis as a substitute for PostgreSQL plus document storage.
