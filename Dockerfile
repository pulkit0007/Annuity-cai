# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables to prevent .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install curl and clean up apt cache to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python -m pip install --upgrade pip

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
RUN pip install --default-timeout=100 --retries=10 --no-cache-dir -r requirements.txt

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
