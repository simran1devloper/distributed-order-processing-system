# --- Stage 1: Build dependencies ---
FROM python:3.11-slim as builder

WORKDIR /build

# Install dependencies into a temporary directory
COPY workers/payment/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Final Runtime ---
FROM python:3.11-slim

WORKDIR /app

# Copy installed libraries from the builder stage
COPY --from=builder /install /usr/local

# Copy the shared logic first (Section 3 & Kafka helpers)
COPY common/ ./common/

# Copy the specific worker code
COPY workers/payment/main.py .

# Environment defaults (can be overridden in docker-compose)
ENV PYTHONUNBUFFERED=1
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:29092
ENV REDIS_URL=redis://redis:6379

# Start the worker
CMD ["python", "main.py"]