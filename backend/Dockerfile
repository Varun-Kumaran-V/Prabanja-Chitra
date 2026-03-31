FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Environment variables with defaults
ENV DATA_DIR=/app/data
ENV HOST=0.0.0.0
ENV PORT=8000

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
