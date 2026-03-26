# ---------- Build stage ----------
FROM rust:1.91.0-alpine3.20 AS builder
# Build dependancies and user managment
RUN apk add --no-cache  \
    shadow  \
    musl-dev \
    gcc \
    && addgroup -g 122 -S appgroup  \
    && adduser -S -u 122 -G appgroup appuser

WORKDIR /app
COPY ./Cargo.toml ./Cargo.toml
COPY ./Cargo.lock ./Cargo.lock
RUN chown -R appuser:appgroup /app
USER 122:122
RUN cargo fetch

COPY ./src ./src
RUN cargo build --release --bin devops-info-service
RUN cargo install --path .

# ---------- Runtime stage ----------
FROM alpine:3.20
# OPTIONAL: PORT {5000}, HOST {0.0.0.0}, DEBUG {false}
LABEL authors="xzsay"
RUN apk add --no-cache shadow \
    && groupadd -g 122 -r appgroup \
    && useradd -u 122 -r -g appgroup -m appuser

WORKDIR /app
COPY --from=builder /app/target/release/devops-info-service ./devops-info-service
RUN chown -R appuser:appgroup /app
USER 122:122

EXPOSE 5000

ENTRYPOINT ["/app/devops-info-service"]
