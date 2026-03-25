FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libpcap-dev \
    tcpdump \
    build-essential \
    curl \
    nmap \
    hping3 \
    openssh-client \
    iputils-arping \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/db

RUN python model/train.py 2>/dev/null || echo "Dataset not found — train manually: docker-compose exec backend python model/train.py"

EXPOSE 5000
CMD ["python", "app.py"]
