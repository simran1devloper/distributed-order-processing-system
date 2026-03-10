FROM python:3.11-slim

WORKDIR /app

# Fix: Point to the api sub-folder
COPY api/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the common folder and the api folder
COPY common/ ./common/
COPY api/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]