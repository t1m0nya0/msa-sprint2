import json
import os
import time
import uuid
from concurrent import futures
from datetime import datetime, timezone

import grpc
import psycopg2
import requests
from kafka import KafkaProducer
from grpc import StatusCode

import booking_pb2
import booking_pb2_grpc

MONOLITH_URL = os.getenv("MONOLITH_URL", "http://hotelio-monolith:8080")
DB_HOST = os.getenv("DB_HOST", "booking-db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "booking")
DB_USER = os.getenv("DB_USER", "booking")
DB_PASSWORD = os.getenv("DB_PASSWORD", "booking")
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


def next_booking_id(cur) -> str:
    cur.execute("SELECT COALESCE(MAX(CAST(id AS BIGINT)), 0) + 1 FROM bookings")
    return str(cur.fetchone()[0])


def init_db():
    for attempt in range(30):
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS bookings (
                            id VARCHAR(64) PRIMARY KEY,
                            user_id VARCHAR(64) NOT NULL,
                            hotel_id VARCHAR(64) NOT NULL,
                            promo_code VARCHAR(64),
                            discount_percent DOUBLE PRECISION DEFAULT 0,
                            price DOUBLE PRECISION NOT NULL,
                            created_at TIMESTAMPTZ DEFAULT NOW()
                        )
                        """
                    )
                conn.commit()
            return
        except psycopg2.OperationalError:
            print(f"DB not ready, retry {attempt + 1}/30...")
            time.sleep(2)
    raise RuntimeError("Cannot connect to booking database")


def monolith_get(path: str):
    resp = requests.get(f"{MONOLITH_URL}{path}", timeout=10)
    resp.raise_for_status()
    return resp.text.strip()


def monolith_post(path: str):
    resp = requests.post(f"{MONOLITH_URL}{path}", timeout=10)
    resp.raise_for_status()
    return resp.json() if resp.content else {}


def validate_user(user_id: str):
    active = monolith_get(f"/api/users/{user_id}/active")
    if active != "true":
        raise ValueError("User is inactive")
    blacklisted = monolith_get(f"/api/users/{user_id}/blacklisted")
    if blacklisted == "true":
        raise ValueError("User is blacklisted")


def validate_hotel(hotel_id: str):
    if monolith_get(f"/api/hotels/{hotel_id}/operational") != "true":
        raise ValueError("Hotel is not operational")
    if monolith_get(f"/api/reviews/hotel/{hotel_id}/trusted") != "true":
        raise ValueError("Hotel is not trusted based on reviews")
    if monolith_get(f"/api/hotels/{hotel_id}/fully-booked") == "true":
        raise ValueError("Hotel is fully booked")


def resolve_base_price(user_id: str) -> float:
    status = monolith_get(f"/api/users/{user_id}/status").strip('"')
    return 80.0 if status.upper() == "VIP" else 100.0


def resolve_promo_discount(promo_code: str | None, user_id: str) -> float:
    if not promo_code:
        return 0.0
    promo = monolith_post(f"/api/promos/validate?code={promo_code}&userId={user_id}")
    return float(promo.get("discount", 0.0))


def publish_event(booking: dict):
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
    payload = json.dumps({**booking, "eventType": "BookingCreated"}).encode("utf-8")
    producer.send(KAFKA_TOPIC, payload)
    producer.flush(10)
    producer.close()


class BookingServiceImpl(booking_pb2_grpc.BookingServiceServicer):
    def CreateBooking(self, request, context):
        try:
            validate_user(request.user_id)
            validate_hotel(request.hotel_id)
            base_price = resolve_base_price(request.user_id)
            discount = resolve_promo_discount(request.promo_code or None, request.user_id)
            final_price = base_price - discount

            with get_conn() as conn:
                with conn.cursor() as cur:
                    booking_id = next_booking_id(cur)
                    created_at = datetime.now(timezone.utc).isoformat()
                    cur.execute(
                        """
                        INSERT INTO bookings
                        (id, user_id, hotel_id, promo_code, discount_percent, price, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            booking_id,
                            request.user_id,
                            request.hotel_id,
                            request.promo_code or None,
                            discount,
                            final_price,
                            created_at,
                        ),
                    )
                conn.commit()

            event = {
                "id": booking_id,
                "userId": request.user_id,
                "hotelId": request.hotel_id,
                "promoCode": request.promo_code or "",
                "discountPercent": discount,
                "price": final_price,
                "createdAt": created_at,
            }
            publish_event(event)

            return booking_pb2.BookingResponse(
                id=booking_id,
                user_id=request.user_id,
                hotel_id=request.hotel_id,
                promo_code=request.promo_code,
                discount_percent=discount,
                price=final_price,
                created_at=created_at,
            )
        except ValueError as exc:
            context.set_code(StatusCode.INVALID_ARGUMENT)
            context.set_details(str(exc))
            return booking_pb2.BookingResponse()
        except Exception as exc:
            context.set_code(StatusCode.INTERNAL)
            context.set_details(str(exc))
            return booking_pb2.BookingResponse()

    def ListBookings(self, request, context):
        query = "SELECT id, user_id, hotel_id, promo_code, discount_percent, price, created_at FROM bookings"
        params: tuple = ()
        if request.user_id:
            query += " WHERE user_id = %s"
            params = (request.user_id,)

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

        bookings = []
        for row in rows:
            created = row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6])
            bookings.append(
                booking_pb2.BookingResponse(
                    id=row[0],
                    user_id=row[1],
                    hotel_id=row[2],
                    promo_code=row[3] or "",
                    discount_percent=float(row[4] or 0),
                    price=float(row[5]),
                    created_at=created,
                )
            )
        return booking_pb2.BookingListResponse(bookings=bookings)


def serve():
    init_db()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    booking_pb2_grpc.add_BookingServiceServicer_to_server(BookingServiceImpl(), server)
    server.add_insecure_port("[::]:9090")
    server.start()
    print("booking-service gRPC listening on :9090")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
