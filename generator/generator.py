import json
import time
import random
from kafka import KafkaProducer
from datetime import datetime
import os
import sys

# Добавляем путь к общему модулю
sys.path.append('/app/common')
from hmac_auth import add_signature

# Настройки Kafka
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
TOPIC = 'raw.events'

# Инициализация продюсера
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Типы событий
EVENT_TYPES = ['login_success', 'login_failed', 'file_access', 'config_change']
SOURCES = ['app-server-1', 'app-server-2', 'db-server-1']

print(f"Generator started. Sending events to {TOPIC} via {KAFKA_BOOTSTRAP_SERVERS}")

while True:
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": random.choice(SOURCES),
        "event_type": random.choice(EVENT_TYPES),
        "value": random.randint(1, 100),
        "user_id": f"user_{random.randint(1, 10)}"
    }

    # Имитация аномального всплеска (5% событий с высоким value)
    if random.random() < 0.05:
        event["value"] = random.randint(200, 500)
        event["event_type"] = "login_failed"  # делаем подозрительным

    # Подписываем сообщение
    signed_event = add_signature(event)

    # Отправляем
    producer.send(TOPIC, signed_event)
    print(f"[Generator] Sent: {signed_event['event_type']} from {signed_event['source']} value={signed_event['value']}")

    time.sleep(0.5)  # 2 события в секунду