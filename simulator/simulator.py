import json
import random
import time
from datetime import datetime, timezone
from google.cloud import pubsub_v1
from dotenv import load_dotenv
import os
import requests

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
TOPIC_ID = "worldcup-sensors"
DT_URL = os.getenv("DYNATRACE_ENV_URL")
DT_TOKEN = os.getenv("DYNATRACE_API_TOKEN")

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

GATES = ["Gate_1", "Gate_2", "Gate_3", "Gate_4", "Gate_5", "Gate_6", "Gate_7", "Gate_8"]
STANDS = ["North", "South", "East", "West"]
SERVICES = ["ticketing", "wifi", "pos_terminal", "security_cam", "pa_system"]

def generate_crowd_data():
    gate = random.choice(GATES)
    density = random.randint(20, 100)
    if random.random() < 0.1:
        density = random.randint(88, 100)
    return {
        "type": "crowd",
        "gate": gate,
        "stand": random.choice(STANDS),
        "density_percent": density,
        "fans_per_minute": random.randint(50, 500),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def generate_infra_data():
    cpu = random.randint(20, 85)
    if random.random() < 0.1:
        cpu = random.randint(88, 100)
    service = random.choice(SERVICES)
    return {
        "type": "infrastructure",
        "service": service,
        "cpu_percent": cpu,
        "memory_percent": random.randint(30, 90),
        "response_time_ms": random.randint(50, 2000),
        "status": "degraded" if cpu > 87 else "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def publish_to_pubsub(data):
    message = json.dumps(data).encode("utf-8")
    future = publisher.publish(topic_path, message)
    return future.result()

def send_to_dynatrace(data):
    """Send metrics to Dynatrace in MINT format"""
    headers = {
        "Authorization": f"Api-Token {DT_TOKEN}",
        "Content-Type": "text/plain"
    }
    
    if data["type"] == "crowd":
        gate = data["gate"].replace("_", "")
        metrics = f'worldcup.crowd.density,gate={gate},stand={data["stand"]} {data["density_percent"]}\n'
        metrics += f'worldcup.crowd.fans_per_minute,gate={gate},stand={data["stand"]} {data["fans_per_minute"]}'
    else:
        service = data["service"]
        metrics = f'worldcup.infra.cpu,service={service} {data["cpu_percent"]}\n'
        metrics += f'worldcup.infra.memory,service={service} {data["memory_percent"]}\n'
        metrics += f'worldcup.infra.response_time,service={service} {data["response_time_ms"]}'

    response = requests.post(
        f"{DT_URL}/api/v2/metrics/ingest",
        headers=headers,
        data=metrics
    )
    return response.status_code

def main():
    print(f"🏟️  World Cup Ops Simulator starting...")
    print(f"📡 Publishing to Pub/Sub: {topic_path}")
    print(f"📊 Sending metrics to Dynatrace: {DT_URL}")
    print(f"Press Ctrl+C to stop\n")

    while True:
        for _ in range(3):
            data = generate_crowd_data()
            publish_to_pubsub(data)
            dt_status = send_to_dynatrace(data)
            print(f"✅ [{data['type']}] Gate={data['gate']} Density={data['density_percent']}% → Dynatrace: {dt_status}")

        for _ in range(2):
            data = generate_infra_data()
            publish_to_pubsub(data)
            dt_status = send_to_dynatrace(data)
            print(f"✅ [{data['type']}] Service={data['service']} CPU={data['cpu_percent']}% → Dynatrace: {dt_status}")

        print(f"\n⏱️  Waiting 30 seconds...\n")
        time.sleep(30)

if __name__ == "__main__":
    main()
