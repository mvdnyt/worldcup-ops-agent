import os
import json
from datetime import datetime, timezone
from google.cloud import pubsub_v1
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
SUBSCRIPTION_ID = "worldcup-sensors-sub"

THRESHOLDS = {
    "crowd_density": 85,
    "cpu_percent": 85,
    "response_time_ms": 1500
}

def check_alerts(message_data):
    alerts = []
    data = json.loads(message_data)

    if data["type"] == "crowd":
        if data["density_percent"] > THRESHOLDS["crowd_density"]:
            alerts.append({
                "type": "CROWD_SURGE",
                "severity": "HIGH" if data["density_percent"] > 95 else "MEDIUM",
                "gate": data["gate"],
                "value": data["density_percent"],
                "threshold": THRESHOLDS["crowd_density"],
                "message": f"Crowd surge at {data['gate']} — {data['density_percent']}% density",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    elif data["type"] == "infrastructure":
        if data["cpu_percent"] > THRESHOLDS["cpu_percent"]:
            alerts.append({
                "type": "INFRA_SPIKE",
                "severity": "HIGH" if data["cpu_percent"] > 95 else "MEDIUM",
                "service": data["service"],
                "value": data["cpu_percent"],
                "threshold": THRESHOLDS["cpu_percent"],
                "message": f"CPU spike on {data['service']} — {data['cpu_percent']}%",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        if data["response_time_ms"] > THRESHOLDS["response_time_ms"]:
            alerts.append({
                "type": "SLOW_RESPONSE",
                "severity": "MEDIUM",
                "service": data["service"],
                "value": data["response_time_ms"],
                "threshold": THRESHOLDS["response_time_ms"],
                "message": f"Slow response on {data['service']} — {data['response_time_ms']}ms",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    return alerts

def callback(message):
    alerts = check_alerts(message.data)
    if alerts:
        for alert in alerts:
            print(f"\n🚨 ALERT [{alert['severity']}] {alert['type']}")
            print(f"   {alert['message']}")
            print(f"   Time: {alert['timestamp']}")
    else:
        data = json.loads(message.data)
        if data["type"] == "crowd":
            print(f"✅ Normal: {data['gate']} density {data['density_percent']}%")
        else:
            print(f"✅ Normal: {data['service']} CPU {data['cpu_percent']}%")
    message.ack()

def main():
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    print(f"🔍 Listening for alerts on {subscription_path}")
    print(f"Press Ctrl+C to stop\n")

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
        print("\nStopped.")

if __name__ == "__main__":
    main()
