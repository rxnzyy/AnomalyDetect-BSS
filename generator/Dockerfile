FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY generator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY generator/generator.py .
COPY common ./common

CMD ["python", "generator.py"]