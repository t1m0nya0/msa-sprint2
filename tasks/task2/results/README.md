# Стратегия миграции данных booking-service

**Автор:** Nurbulatuly Tamirlan

## As-Is (при запуске)

- Бронирования хранились только в PostgreSQL монолита (`booking` table).
- `POST /api/bookings` обрабатывался внутри монолита.

## Промежуточное состояние (To-Be, текущий спринт)

1. **Create path** — монолит проксирует создание в `booking-service` по gRPC (Strangler Fig).
2. **Read path** — `GET /api/bookings?userId=...` также идёт в gRPC (ограничение `GrpcBookingService`).
3. **Отдельная БД** — `booking-db` для новых записей; монолитная БД остаётся для users/hotels/promos/reviews.
4. **События** — каждое создание публикуется в Kafka (`booking-created`), `booking-history-service` строит read-модель без доступа к боевой БД.

## Миграция исторических данных

- Batch-скрипт копирует существующие строки из `monolith.booking` в `booking-service.bookings` с сохранением numeric ID.
- На время миграции — dual-read недоступен для `GET` без `userId` (известное ограничение прокси).
- Новые записи создаются только в booking-service.

## Дальнейшие шаги

- CDC (Debezium) или Outbox для синхронизации.
- Полный отказ от таблицы `booking` в монолите после стабилизации.
