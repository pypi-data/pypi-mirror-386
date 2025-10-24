# For no geospatial applications
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1

RUN apt update && apt install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Set a non-root user and group (optional but recommended for security)
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Change ownership of the application files to the non-root user
RUN chown -R appuser:appuser /app

# Set the user to use for running the application
USER appuser

CMD ["sh", "-c", "/app/wait_for_rabbitmq.sh && celery -A src.celery.app worker --loglevel=info --concurrency=4 & python run.py"]

#For geospatial applications

# FROM python:latest
# ENV PYTHONUNBUFFERED=1
# # Install netcat-openbsd and other dependencies
# RUN apt update && apt install -y gdal-bin netcat-openbsd
# # Set a non-root user and group (optional but recommended for security)
# RUN groupadd -r appuser && useradd -r -g appuser appuser
# WORKDIR /app
# # Copy requirements.txt and install dependencies
# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt
# RUN pip install --no-cache-dir --force-reinstall bcrypt passlib
# # Copy the rest of the application code
# COPY . .
# # Copy wait_for_rabbitmq.sh script to container with root user
# USER root
# COPY wait_for_rabbitmq.sh /app/wait_for_rabbitmq.sh
# RUN chmod +x /app/wait_for_rabbitmq.sh
# # Change ownership of the application files to the non-root user
# RUN chown -R appuser:appuser /app
# # Set the user to use for running the application
# USER appuser
# # Command to run FastAPI and Celery worker
# CMD ["sh", "-c", "/app/wait_for_rabbitmq.sh && celery -A src.celery.app worker --loglevel=info --concurrency=4 & uvicorn app:app --host 0.0.0.0 --port 8083"]