FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY main.go .
RUN CGO_ENABLED=0 go build -o /booking-service main.go

FROM alpine:3.19
WORKDIR /app
COPY --from=builder /booking-service .
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD wget -qO- http://localhost:8080/ping || exit 1
CMD ["./booking-service"]
