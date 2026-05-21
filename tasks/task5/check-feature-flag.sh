#!/bin/bash

set -e

KUBECTL="${KUBECTL:-kubectl}"

echo "▶️ Проверка Feature Flag (X-Feature-Enabled: true)..."

RESP=$($KUBECTL exec deployment/booking-service-v1 -c booking-service -- \
  wget -qO- --header="X-Feature-Enabled: true" http://booking-service/ping)

echo "Response: $RESP"
echo "$RESP" | grep -q "pong-v2-feature" && echo "[PASS] Feature flag routing OK" || exit 1
