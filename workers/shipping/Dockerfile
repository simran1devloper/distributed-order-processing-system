# --- Stage 1: Build dependencies (Halwai stage - sirf saman taiyar karna) ---
FROM python:3.11-slim as builder

WORKDIR /build

# Requirements copy karo aur install karo ek alag folder (/install) mein
COPY workers/shipping/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Final Runtime (Serving stage - sirf kaam ki cheezein) ---
FROM python:3.11-slim

WORKDIR /app

# Builder stage se sirf installed libraries uthao (Image halki rahegi)
COPY --from=builder /install /usr/local

# Shared logic (The Rulebook) copy karo
COPY common/ ./common/

# Shipping ka asli code copy karo
COPY workers/shipping/main.py .

# Environment settings (Docker logs turant dikhne ke liye)
ENV PYTHONUNBUFFERED=1
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:29092
ENV REDIS_URL=redis://redis:6379

# Worker ko start karo
CMD ["python", "main.py"]