FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код сервиса и общий модуль
COPY generator.py .
COPY ../common /app/common

# Запуск
CMD ["python", "generator.py"]