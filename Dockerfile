FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

# cài tesseract + phụ thuộc cho opencv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-vie \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy requirements và cài
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# copy toàn bộ mã nguồn
COPY . /app

# biến môi trường để receipt_processor dùng
ENV TESSERACT_CMD=/usr/bin/tesseract
ENV ENV=production

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]