FROM rust:1.82-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache musl-dev

# Copy manifests
COPY Cargo.toml Cargo.lock* ./

# Create dummy source to build dependencies
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release || true

# Copy actual source
COPY src ./src

# Build for release
RUN cargo build --release

# Runtime stage
FROM alpine:latest

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/target/release/hungarian-benchmark .

# Create results directory
RUN mkdir -p /results
