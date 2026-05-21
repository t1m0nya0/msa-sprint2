# Task 3: GraphQL Federation — отчёт

**Автор:** Nurbulatuly Tamirlan

## Изменения

### booking-subgraph
- Подключён gRPC к `booking-service:9090` (ListBookings).
- ACL: заголовок `userid` должен совпадать с `userId` в запросе.
- При нарушении ACL возвращается **GraphQL-ошибка** (`FORBIDDEN` / `UNAUTHENTICATED`), а не пустой список — чтобы отличить «нет данных» от «нет доступа».
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

### ACL deny (чужой userid)

```bash
curl -X POST http://localhost:4000/ \
  -H "Content-Type: application/json" \
  -H "userid: test-user-3" \
  -d '{"query":"query { bookingsByUser(userId: \"test-user-2\") { id } }"}'
```

Ожидаемый ответ — поле `errors` с `extensions.code: FORBIDDEN` (см. `acl-deny-response.json`, скриншот Playground: `acl-deny-screenshot.png`).

Артефакты: `report.txt`, `acl-deny-response.json`, `acl-deny-screenshot.png`, `docker-ps.txt`.
