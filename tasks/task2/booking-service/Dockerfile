FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY booking.proto .
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. booking.proto

COPY server.py .

EXPOSE 9090

CMD ["python", "server.py"]
