# Task 3: GraphQL Federation — отчёт

**Автор:** Nurbulatuly Tamirlan

## Изменения

### booking-subgraph
- Подключён gRPC к `booking-service:9090` (ListBookings).
- ACL: заголовок `userid` должен совпадать с `userId` в запросе.
- Federation: поле `hotel` резолвится через reference на hotel-subgraph.

### hotel-subgraph
- `__resolveReference` и `hotelsByIds` вызывают REST монолита `/api/hotels/{id}`.
- `name` формируется из description отеля.

### apollo-gateway
- `RemoteGraphQLDataSource` пробрасывает заголовок `userid` в подграфы.

## Проверка

```bash
cd tasks/task3 && docker compose up -d --build
curl -X POST http://localhost:4000/ \
  -H "Content-Type: application/json" \
  -H "userid: test-user-2" \
  -d '{"query":"query { bookingsByUser(userId: \"test-user-2\") { id hotel { name city } discountPercent } }"}'
```

Артефакты: `report.txt`, `docker-ps.txt`, логи в report.
