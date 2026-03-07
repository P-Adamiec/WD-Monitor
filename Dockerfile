FROM python:3.11-slim

WORKDIR /app

# Ensure we have required curl libs for curl_cffi and CA certificates
RUN apt-get update && \
    apt-get install -y curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

CMD ["python", "run.py"]
