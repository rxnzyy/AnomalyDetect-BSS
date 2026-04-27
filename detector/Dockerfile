FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY detector.py .
COPY ../common /app/common

CMD ["python", "detector.py"]