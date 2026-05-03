from kafka import KafkaConsumer
import json
import os
import requests
import sys
import time

sys.path.append('/app')
from common.hmac_auth import verify_signature

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
TOPIC = 'anomalies'

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

print(f"Alerter starting. Connecting to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")

# Ожидание доступности Kafka
while True:
    try:
        consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest'
        )
        print("Connected to Kafka")
        break
    except Exception as e:
        print(f"Waiting for Kafka... {e}")
        time.sleep(5)

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("[Alerter] Telegram not configured (missing token or chat_id)")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            print("[Alerter] Telegram notification sent")
            return True
        else:
            print(f"[Alerter] Telegram error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[Alerter] Telegram exception: {e}")
        return False

print(f"Alerter started. Listening to {TOPIC}")

for msg in consumer:
    anomaly = msg.value

    if not verify_signature(anomaly):
        print(f"[Alerter] Invalid anomaly signature, skipping")
        continue

    alert_text = (
        f"🚨 <b>SECURITY ALERT</b> 🚨\n\n"
        f"<b>Type:</b> {anomaly.get('anomaly_type', 'unknown')}\n"
        f"<b>Severity:</b> {anomaly.get('severity', 0)}/5\n"
        f"<b>Description:</b> {anomaly.get('description', '')}\n"
        f"<b>Source:</b> {anomaly.get('source', 'unknown')}\n"
        f"<b>Time:</b> {anomaly.get('timestamp', '')}"
    )

    print(f"[Alerter] Alert: {alert_text}")
    send_telegram(alert_text)