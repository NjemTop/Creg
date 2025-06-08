#!/usr/bin/env bash
# wait-for-it.sh: ожидание, пока указанный TCP host:port станет доступен.

HOST="$1"
PORT="$2"
shift 2

TIMEOUT=30
SLEEP=1

echo "Waiting for $HOST:$PORT to be ready..."

for i in $(seq 1 $TIMEOUT); do
  nc -z "$HOST" "$PORT" && break
  echo "Connection to $HOST:$PORT failed (attempt $i). Sleeping $SLEEP sec."
  sleep $SLEEP
done

if ! nc -z "$HOST" "$PORT"; then
  echo "Timeout after ${TIMEOUT}s waiting for $HOST:$PORT"
  exit 1
fi

echo "$HOST:$PORT is available!"
exec "$@"
