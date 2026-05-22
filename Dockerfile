# tdxrs — multi-stage Docker build for Linux wheel
#
# Build:
#   docker build -t tdxrs .
#   docker run --rm tdxrs
#
# Extract wheel:
#   docker build --output . .

# === Stage 1: Build ===
FROM python:3.13-slim AS builder

# Install Rust toolchain
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential pkg-config libssl-dev && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.cargo/bin:${PATH}"

RUN pip install --no-cache-dir maturin

WORKDIR /app
# Copy only what's needed for the build (see .dockerignore)
COPY Cargo.toml Cargo.lock ./
COPY src/ src/
COPY python/ python/

# Build the native extension in a venv
RUN python -m venv .venv && \
    . .venv/bin/activate && \
    maturin develop --release

# === Stage 2: Test image ===
FROM python:3.13-slim
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}"
CMD ["python", "-c", "import tdxrs; print('tdxrs OK')"]
