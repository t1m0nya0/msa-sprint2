import json
import os
import time

import psycopg2
from kafka import KafkaConsumer

DB_HOST = os.getenv("DB_HOST", "booking-history-db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "history")
DB_USER = os.getenv("DB_USER", "history")
DB_PASSWORD = os.getenv("DB_PASSWORD", "history")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "booking-created")


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def init_db():
    for attempt in range(30):
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS booking_history (
                            id SERIAL PRIMARY KEY,
                            booking_id VARCHAR(64) NOT NULL,
                            user_id VARCHAR(64) NOT NULL,
                            hotel_id VARCHAR(64) NOT NULL,
                            promo_code VARCHAR(64),
                            discount_percent DOUBLE PRECISION DEFAULT 0,
                            price DOUBLE PRECISION NOT NULL,
                            booking_date DATE NOT NULL,
                            created_at TIMESTAMPTZ DEFAULT NOW()
                        )
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS booking_stats_daily (
                            stat_date DATE NOT NULL,
                            user_id VARCHAR(64) NOT NULL,
                            hotel_id VARCHAR(64) NOT NULL,
                            bookings_count INT DEFAULT 0,
                            total_revenue DOUBLE PRECISION DEFAULT 0,
                            PRIMARY KEY (stat_date, user_id, hotel_id)
                        )
                        """
                    )
                conn.commit()
            return
        except psycopg2.OperationalError:
            print(f"DB not ready, retry {attempt + 1}/30...")
            time.sleep(2)
    raise RuntimeError("Cannot connect to history database")


def save_event(event: dict):
    booking_date = event.get("createdAt", "")[:10]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO booking_history
                (booking_id, user_id, hotel_id, promo_code, discount_percent, price, booking_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event["id"],
                    event["userId"],
                    event["hotelId"],
                    event.get("promoCode") or None,
                    event.get("discountPercent", 0),
                    event.get("price", 0),
                    booking_date,
                ),
            )
            cur.execute(
                """
                INSERT INTO booking_stats_daily (stat_date, user_id, hotel_id, bookings_count, total_revenue)
                VALUES (%s, %s, %s, 1, %s)
                ON CONFLICT (stat_date, user_id, hotel_id)
                DO UPDATE SET
                    bookings_count = booking_stats_daily.bookings_count + 1,
                    total_revenue = booking_stats_daily.total_revenue + EXCLUDED.total_revenue
                """,
                (booking_date, event["userId"], event["hotelId"], event.get("price", 0)),
            )
        conn.commit()
    print(f"Saved booking history for {event['id']}")


def consume():
    init_db()
    while True:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                auto_offset_reset="earliest",
                group_id="booking-history-group",
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )
            print(f"Listening to {KAFKA_TOPIC} on {KAFKA_BOOTSTRAP}")
            for message in consumer:
                save_event(message.value)
        except Exception as exc:
            print(f"Consumer error: {exc}, retrying in 5s...")
            time.sleep(5)


if __name__ == "__main__":
    consume()
