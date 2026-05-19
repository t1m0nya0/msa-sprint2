# MSA Sprint 2 — Hotelio (Nurbulatuly Tamirlan)

Репозиторий: https://github.com/t1m0nya0/msa-sprint2

## Структура

| Папка | Содержание |
|-------|------------|
| `tasks/task1/results/` | ADR, PlantUML диаграмма, test-log |
| `tasks/task2/` | booking-service (Python/gRPC), booking-history-service, Kafka |
| `tasks/task2/results/` | regress.sh, test-log, db-dump, README |
| `tasks/task3/` | GraphQL Federation (booking + hotel subgraphs, gateway) |
| `tasks/task3/results/` | report, скриншоты/логи GraphQL |
| `tasks/task4/` | Go REST-сервис, Helm, GitLab CI |
| `tasks/task5/results/` | Istio: VirtualService, DestinationRule, EnvoyFilter |

## Запуск (всё в Docker)

```bash
docker network create hotelio-net  # один раз

# Task 2
cd tasks/task2 && docker compose up -d --build

# Тесты
docker run --rm --network hotelio-net --entrypoint bash \
  -v $(pwd)/tasks/task2/results/regress.sh:/app/regress.sh \
  -v $(pwd)/tasks/task2/results/init-fixtures.sql:/app/init-fixtures.sql \
  -e DB_HOST=hotelio-db -e DB_USER=hotelio -e DB_PASSWORD=hotelio -e DB_NAME=hotelio \
  -e API_URL=http://hotelio-monolith:8080 \
  hotelio-tester /app/regress.sh

# Task 3 (нужен task2)
cd tasks/task3 && docker compose up -d --build
```

## K8s / Istio (dev-контейнер)

```bash
docker build -t msa-dev-env dev-env/
docker run --rm -it --privileged \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/workspace msa-dev-env bash
```

Внутри: `minikube start`, `gitlab-ci-local`, `helm upgrade`, Istio — см. `dev-env/README.md`.

## Сдача

1. Закоммить все изменения
2. Создать PR в `main`
3. Отправить ссылку на PR в Практикуме
