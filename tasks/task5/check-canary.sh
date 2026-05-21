#!/bin/bash

set -e

KUBECTL="${KUBECTL:-kubectl}"

echo "▶️ Checking canary release (90% v1, 10% v2) via service mesh..."

$KUBECTL exec deployment/booking-service-v1 -c booking-service -- sh -c '
  v1=0; v2=0
  for i in $(seq 1 100); do
    r=$(wget -qO- http://booking-service/ping 2>/dev/null)
    case "$r" in pong-v2*) v2=$((v2+1)) ;; *) v1=$((v1+1)) ;; esac
  done
  echo "v1=$v1 v2=$v2"
  if [ "$v1" -ge 70 ] && [ "$v2" -ge 2 ]; then
    echo "[PASS] Canary split looks correct"
  else
    echo "[FAIL] Unexpected split"
    exit 1
  fi
'
