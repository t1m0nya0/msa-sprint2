#!/bin/bash

set -e

KUBECTL="${KUBECTL:-kubectl}"

echo "▶️ Testing fallback route (kill one v1 pod)..."

POD=$($KUBECTL get pods -l app=booking-service,version=v1 -o jsonpath='{.items[0].metadata.name}')
echo "Deleting pod: $POD"
$KUBECTL delete pod "$POD" --grace-period=0 --force
sleep 8

$KUBECTL exec deployment/booking-service-v2 -c booking-service -- sh -c '
  for i in 1 2 3 4 5; do
    wget -qO- http://booking-service/ping || exit 1
  done
  echo "[PASS] Fallback route working"
'
