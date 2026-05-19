# Task 5: Istio Service Mesh для booking-service

**Автор:** Nurbulatuly Tamirlan

## Изменения

- Helm-чарт доработан: оба deployment (`booking-service-v1`, `booking-service-v2`) используют общий label `app: booking-service` и единый Service `booking-service`.
- Subsets v1/v2 задаются label `version`.
- VirtualService: canary 90/10, feature-flag маршрут при `X-Feature-Enabled: true`, retry.
- DestinationRule: subsets v1/v2, circuit breaking (outlierDetection).
- EnvoyFilter: дополнительная маршрутизация на v2 при feature flag.

## Деплой

```bash
istioctl install --set profile=demo -y
kubectl label namespace default istio-injection=enabled --overwrite

docker build -t booking-service:latest booking-service/
minikube image load booking-service:latest

helm upgrade --install booking-v1 helm/booking-service -f results/values-v1.yaml
helm upgrade --install booking-v2 helm/booking-service -f results/values-v2.yaml

kubectl apply -f results/destination-rule.yaml
kubectl apply -f results/virtual-service.yaml
kubectl apply -f results/envoy-filter.yaml

export KUBECTL=kubectl  # или полный путь
./check-istio.sh
./check-canary.sh
./check-fallback.sh
./check-feature-flag.sh
```

## Результаты проверок

- **check-istio**: pods istio-system Running, injection=enabled
- **check-canary**: ~90% `pong` (v1), ~10% `pong-v2` (v2)
- **check-feature-flag**: `pong-v2-feature` при заголовке `X-Feature-Enabled: true`
- **check-fallback**: после удаления одного v1-pod запросы продолжают работать

Логи: `results/check-scripts-log.txt`
