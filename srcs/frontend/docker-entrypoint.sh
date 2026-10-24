#!/bin/sh
set -eu

cd /app

# Reinstall dependencies only when the lockfile changes.
LOCK_HASH="$(sha256sum package-lock.json | cut -d ' ' -f 1)"
HASH_FILE="node_modules/.package-lock.sha256"

if [ ! -f "$HASH_FILE" ] || [ "$(cat "$HASH_FILE")" != "$LOCK_HASH" ]; then
    echo "Installing frontend dependencies..."
    npm ci
    printf '%s' "$LOCK_HASH" > "$HASH_FILE"
fi

exec npm run dev -- --host 0.0.0.0 --force
