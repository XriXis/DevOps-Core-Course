# ---------- Build stage ----------
FROM rust:1.91.0-alpine3.20 AS builder
# Build dependancies and user managment
RUN apk add --no-cache  \
    shadow  \
    musl-dev \
    gcc \
    && addgroup -S appgroup  \
    && adduser -S appuser -G appgroup

USER appuser
WORKDIR /app
COPY ./Cargo.toml ./Cargo.toml
COPY ./Cargo.lock ./Cargo.lock
RUN cargo fetch

COPY ./src ./src
RUN cargo build --release --bin devops-info-service
RUN cargo install --path .

# ---------- Runtime stage ----------
FROM alpine:3.20
# OPTIONAL: PORT {5000}, HOST {0.0.0.0}, DEBUG {false}
LABEL authors="xzsay"
RUN apk add --no-cache shadow \
    && groupadd -r appgroup \
    && useradd -r -g appgroup -m appuser
USER appuser

WORKDIR /app
COPY --from=builder /app/target/release/devops-info-service ./devops-info-service

EXPOSE 5000

ENTRYPOINT ["/app/devops-info-service"]
