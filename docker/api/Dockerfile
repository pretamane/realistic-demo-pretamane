# Enhanced FastAPI Application - Production Docker Image
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the enhanced application
COPY enhanced_app.py .

# Create necessary directories for EFS mounts
RUN mkdir -p /mnt/efs/uploads /mnt/efs/processed /mnt/efs/logs

# Expose port for FastAPI
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the enhanced app with uvicorn
CMD ["uvicorn", "enhanced_app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
