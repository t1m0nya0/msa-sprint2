#!/bin/bash

set -e

KUBECTL="${KUBECTL:-kubectl}"

echo "▶️ Проверка установки Istio..."
$KUBECTL get pods -n istio-system

echo "▶️ Проверка Istio инъекции в default namespace..."
$KUBECTL get namespace default -o jsonpath='{.metadata.labels.istio-injection}'
echo

echo "▶️ Поды booking-service с sidecar:"
$KUBECTL get pods -l app=booking-service
