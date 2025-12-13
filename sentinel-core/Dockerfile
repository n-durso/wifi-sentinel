FROM python:3.10-slim

# Aggiorno pacchetti
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Copio requirements
COPY requirements.txt .

# Installo librerie Python
RUN pip install --no-cache-dir -r requirements.txt

# Copio tutto il codice
COPY . .

# Avvio il subscriber (entrypoint del core)
CMD ["python", "subscriber.py"]
