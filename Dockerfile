FROM python:3.11-slim

# Install system dependencies needed for compiling certain Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy and install dependencies first to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY ./app /app

# Expose NiceGUI's default port
EXPOSE 80

# Run NiceGUI on port 80 and make it accessible outside the container
CMD ["python", "main.py", "--port", "80", "--host", "0.0.0.0"]
