import json
import random
import time
from datetime import datetime, timezone
from google.cloud import pubsub_v1
from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
TOPIC_ID = "worldcup-sensors"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

GATES = ["Gate_1", "Gate_2", "Gate_3", "Gate_4", "Gate_5", "Gate_6", "Gate_7", "Gate_8"]
STANDS = ["North", "South", "East", "West"]

def generate_crowd_data():
    gate = random.choice(GATES)
    density = random.randint(20, 100)
    
    # Occasionally simulate a surge
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
    
    # Occasionally simulate a spike
    if random.random() < 0.1:
        cpu = random.randint(88, 100)
    
    return {
        "type": "infrastructure",
        "service": random.choice(["ticketing", "wifi", "pos_terminal", "security_cam", "pa_system"]),
        "cpu_percent": cpu,
        "memory_percent": random.randint(30, 90),
        "response_time_ms": random.randint(50, 2000),
        "status": "degraded" if cpu > 87 else "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def publish_message(data):
    message = json.dumps(data).encode("utf-8")
    future = publisher.publish(topic_path, message)
    print(f"Published [{data['type']}] → {json.dumps(data, indent=2)}")
    return future.result()

def main():
    print(f"🏟️  World Cup Ops Simulator starting...")
    print(f"📡 Publishing to: {topic_path}")
    print(f"Press Ctrl+C to stop\n")
    
    while True:
        # Publish 3 crowd readings and 2 infra readings every cycle
        for _ in range(3):
            publish_message(generate_crowd_data())
        for _ in range(2):
            publish_message(generate_infra_data())
            
        print(f"\n⏱️  Waiting 30 seconds...\n")
        time.sleep(30)

if __name__ == "__main__":
    main()