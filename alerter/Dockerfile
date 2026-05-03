FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY alerter/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alerter/alerter.py .
COPY common ./common

CMD ["python", "alerter.py"]