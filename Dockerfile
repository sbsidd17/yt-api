FROM python:3.11-slim-bullseye

WORKDIR /app

# Install system dependencies including ffmpeg and other required packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
