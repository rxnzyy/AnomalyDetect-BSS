from kafka import KafkaConsumer, KafkaProducer
import json
import os
from collections import defaultdict
from datetime import datetime
import sys
import time

sys.path.append('anomaly_detection\common')
from hmac_auth import verify_signature

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
INPUT_TOPIC = 'raw.events'
OUTPUT_TOPIC = 'anomalies'

# Параметры детектора
WINDOW_SECONDS = 5
THRESHOLD = 30  # событий одного типа за окно

consumer = KafkaConsumer(
    INPUT_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print(f"Detector started. Listening {INPUT_TOPIC} -> {OUTPUT_TOPIC}")

event_counter = defaultdict(int)
last_reset = time.time()

for msg in consumer:
    event = msg.value

    # Проверка HMAC подписи
    if not verify_signature(event):
        print(f"[Detector] Invalid signature, skipping: {event.get('event_type')}")
        continue

    event_type = event['event_type']
    event_counter[event_type] += 1

    # Сброс окна
    now = time.time()
    if now - last_reset >= WINDOW_SECONDS:
        # Проверяем аномалии перед сбросом
        for etype, count in event_counter.items():
            if count > THRESHOLD:
                anomaly = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": event.get('source', 'unknown'),
                    "anomaly_type": "frequency_burst",
                    "severity": 4,
                    "description": f"{etype} occurred {count} times in last {WINDOW_SECONDS}s (threshold={THRESHOLD})",
                    "original_event_snapshot": {
                        "event_type": etype,
                        "source": event.get('source')
                    }
                }
                # Подписываем аномалию (используем ту же функцию, но импортируем)
                from hmac_auth import add_signature

                signed_anomaly = add_signature(anomaly)
                producer.send(OUTPUT_TOPIC, signed_anomaly)
                print(f"[Detector] !! ANOMALY: {anomaly['description']}")

        # Сброс счётчиков
        event_counter.clear()
        last_reset = now