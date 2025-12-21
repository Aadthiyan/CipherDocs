# Root Dockerfile - delegates to backend/Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Copy backend files
COPY backend/ /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run migrations and start server
CMD ["gunicorn", "main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "4", "--bind", "0.0.0.0:$PORT"]
