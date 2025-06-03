#!/bin/bash

BACKUP_DIR="./pgbackups"
LATEST_DUMP=$(ls -t ${BACKUP_DIR}/windmill_*.dump 2>/dev/null | head -n1)

if [ -z "$LATEST_DUMP" ]; then
  echo "❌ No dump found in ${BACKUP_DIR}"
  exit 1
fi

echo "♻️ Restoring dump: $LATEST_DUMP"
docker exec -i windmill-db bash -c "PGPASSWORD=windmill dropdb -U windmill windmill && createdb -U windmill windmill"
cat "$LATEST_DUMP" | docker exec -i windmill-db pg_restore -U windmill -d windmill --no-owner

echo "✅ Restore complete"
