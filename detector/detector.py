from kafka import KafkaConsumer, KafkaProducer
import json
import os
from collections import defaultdict
from datetime import datetime
import sys
import time

sys.path.append('/app')
from common.hmac_auth import verify_signature, add_signature
from influxdb import InfluxDBClient

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
INPUT_TOPIC = 'raw.events'
OUTPUT_TOPIC = 'anomalies'

INFLUXDB_HOST = 'influxdb'
INFLUXDB_PORT = 8086
INFLUXDB_DATABASE = 'metrics'

# ВРЕМЕННО СНИЖЕННЫЙ ПОРОГ ДЛЯ ТЕСТА
WINDOW_SECONDS = 5
THRESHOLD = 5  # Временно 5 вместо 30

print(f"Detector starting. Connecting to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")

while True:
    try:
        consumer = KafkaConsumer(
            INPUT_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='anomaly-detector'
        )
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print("Connected to Kafka")
        break
    except Exception as e:
        print(f"Waiting for Kafka... {e}")
        time.sleep(5)

try:
    influx_client = InfluxDBClient(
        host=INFLUXDB_HOST,
        port=INFLUXDB_PORT,
        database=INFLUXDB_DATABASE
    )
    influx_client.create_database(INFLUXDB_DATABASE)
    print(f"Connected to InfluxDB 1.8, database '{INFLUXDB_DATABASE}' ready")
except Exception as e:
    print(f"Warning: Could not connect to InfluxDB: {e}")
    influx_client = None

print(f"Detector started. Listening {INPUT_TOPIC} -> {OUTPUT_TOPIC}")
print(f"Detection parameters: window={WINDOW_SECONDS}s, threshold={THRESHOLD} events per type")

event_counter = defaultdict(int)
last_reset = time.time()
event_count_since_last = 0

for msg in consumer:
    event = msg.value

    print(f"[Detector] Received event: {event.get('event_type')} from {event.get('source')}")

    if not verify_signature(event):
        print(f"[Detector] Invalid signature, skipping")
        continue

    event_type = event['event_type']
    event_counter[event_type] += 1
    event_count_since_last += 1

    # Отладка: показываем текущие счётчики
    print(f"[Detector] Counters: {dict(event_counter)}")

    if influx_client:
        try:
            point = {
                "measurement": "events",
                "tags": {
                    "event_type": event_type,
                    "source": event.get('source', 'unknown')
                },
                "fields": {
                    "value": event.get('value', 1)
                },
                "time": datetime.utcnow().isoformat()
            }
            influx_client.write_points([point])
        except Exception as e:
            print(f"[Detector] InfluxDB write error: {e}")

    now = time.time()
    if now - last_reset >= WINDOW_SECONDS:
        print(f"[Detector] Window reset. Checking {len(event_counter)} event types...")

        for etype, count in event_counter.items():
            print(f"[Detector] Type '{etype}': count={count}, threshold={THRESHOLD}")
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
                signed_anomaly = add_signature(anomaly)
                producer.send(OUTPUT_TOPIC, signed_anomaly)
                print(f"[Detector] 🚨 ANOMALY DETECTED: {anomaly['description']}")

                if influx_client:
                    try:
                        anomaly_point = {
                            "measurement": "anomalies",
                            "tags": {
                                "anomaly_type": anomaly['anomaly_type']
                            },
                            "fields": {
                                "severity": anomaly['severity']
                            },
                            "time": datetime.utcnow().isoformat()
                        }
                        influx_client.write_points([anomaly_point])
                    except Exception as e:
                        print(f"[Detector] InfluxDB anomaly write error: {e}")
            else:
                print(f"[Detector] Type '{etype}': count={count} <= threshold={THRESHOLD} - no anomaly")

        if influx_client and event_count_since_last > 0:
            try:
                rate_point = {
                    "measurement": "events_rate",
                    "tags": {},
                    "fields": {
                        "count_per_window": event_count_since_last
                    },
                    "time": datetime.utcnow().isoformat()
                }
                influx_client.write_points([rate_point])
            except Exception as e:
                print(f"[Detector] InfluxDB rate write error: {e}")

        event_counter.clear()
        last_reset = now
        event_count_since_last = 0