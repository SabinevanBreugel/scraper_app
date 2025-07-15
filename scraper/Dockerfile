FROM python:3.11-slim

WORKDIR /app

# Installeer dependencies voor psycopg (libpq-dev + build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*
       
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x wait-for-it.sh

ENV PYTHONPATH=/app

ENTRYPOINT ["./wait-for-it.sh", "selenium:4444", "--","python", "run.py"]
CMD ["--scraper_name=vacancy", "--env=dev"]