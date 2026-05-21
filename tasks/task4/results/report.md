# Task 4: CI/CD + Helm + Kubernetes

**Автор:** Nurbulatuly Tamirlan

## Реализация

- **booking-service** (Go): `/ping`, `/ready`, `/feature` при `ENABLE_FEATURE_X=true`.
- **Helm chart**: Deployment с liveness/readiness probes, Service ClusterIP 80→8080.
- **values-staging.yaml** / **values-prod.yaml**: разные replicaCount и resources.
- **.gitlab-ci.yml**: build → test → deploy (minikube image load + helm upgrade) → tag.

## Проверка

```bash
# CI stages (build + test)
docker build -t booking-service:latest booking-service/
docker run -d --name booking-test -p 18080:8080 booking-service:latest
curl http://localhost:18080/ping   # pong
curl http://localhost:18080/ready  # ready

# Minikube deploy
minikube image load booking-service:latest
helm upgrade --install booking-service helm/booking-service
./check-status.sh
./check-dns.sh
```

## Артефакты

| Файл | Содержание |
|------|------------|
| `ci-log.txt` | build + test |
| `k8s-verify-final.txt` | pods, svc, curl /ping |
| `k8s-curl-ping.txt` | port-forward ping |
| `k8s-check-dns.txt` | in-cluster DNS |
| `values-staging.yaml`, `values-prod.yaml` | окружения |

Логи успешной проверки сохранены в `results/`.
