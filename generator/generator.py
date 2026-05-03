import json
import time
import random
from kafka import KafkaProducer
from datetime import datetime
import os
import sys

# Добавляем путь к общему модулю
sys.path.append('/app')
from common.hmac_auth import add_signature

# Настройки Kafka из переменных окружения
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
TOPIC = 'raw.events'

# Типы событий и источники
EVENT_TYPES = ['login_success', 'login_failed', 'file_access', 'config_change']
SOURCES = ['app-server-1', 'app-server-2', 'db-server-1']

print(f"Generator starting. Connecting to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")

# Ожидание доступности Kafka с повторными попытками
while True:
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print("Connected to Kafka")
        break
    except Exception as e:
        print(f"Waiting for Kafka... {e}")
        time.sleep(5)

print("Generator started. Sending events...")

# Основной цикл генерации событий
while True:
    # Формируем обычное событие
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": random.choice(SOURCES),
        "event_type": random.choice(EVENT_TYPES),
        "value": random.randint(1, 100),
        "user_id": f"user_{random.randint(1, 10)}"
    }

    # Имитация аномалии в 10% случаев для более частого тестирования
    if random.random() < 0.1:
        event["value"] = random.randint(200, 500)
        event["event_type"] = "login_failed"

    # Подписываем событие HMAC
    signed_event = add_signature(event)

    # Отправляем в Kafka
    producer.send(TOPIC, signed_event)
    print(f"[Generator] Sent: {event['event_type']} from {event['source']} value={event['value']}")

    # Пауза 0.5 секунды (2 события в секунду)
    time.sleep(0.5)