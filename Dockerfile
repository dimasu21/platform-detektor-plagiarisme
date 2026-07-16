FROM python:3.11-slim

# Install system dependencies for OCR and PDF processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ind \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload directories
RUN mkdir -p static/uploads/highlighted static/uploads/batch_results

# Set environment variables for Linux paths
ENV TESSERACT_CMD=/usr/bin/tesseract
ENV POPPLER_PATH=
ENV FLASK_ENV=production
ENV OMP_THREAD_LIMIT=1

EXPOSE 8000

# Run with gunicorn (production WSGI server)
# --timeout 120: allow long OCR processing
# -w 4: 4 worker processes
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "--timeout", "600", "app:app"]
