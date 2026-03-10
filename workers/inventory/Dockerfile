# Use a slim python image for production
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY workers/inventory/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final Stage
FROM python:3.11-slim
WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy the shared logic and the specific worker code
COPY common/ ./common/
COPY workers/inventory/main.py .

# Run the worker
CMD ["python", "main.py"]