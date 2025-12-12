FROM python:3.10-slim

# Installo nmcli e driver necessari
RUN apt-get update && \
    apt-get install -y network-manager wireless-tools && \
    apt-get clean

# Creazione cartella app
WORKDIR /app

# Copio requirements
COPY requirements.txt .

# Installo librerie Python
RUN pip install --no-cache-dir -r requirements.txt

# Copio il codice
COPY . .

# Comando di avvio
CMD ["python", "monitor.py"]
