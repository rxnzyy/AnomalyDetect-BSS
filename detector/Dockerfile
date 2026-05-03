FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY detector/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY detector/detector.py .
COPY common ./common

CMD ["python", "detector.py"]