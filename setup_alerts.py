import requests
import os
from dotenv import load_dotenv

load_dotenv()

DT_URL = os.getenv("DYNATRACE_ENV_URL")
DT_TOKEN = os.getenv("DYNATRACE_API_TOKEN")

headers = {
    "Authorization": f"Api-Token {DT_TOKEN}",
    "Content-Type": "application/json"
}

alerts = [
    {
        "title": "Critical Crowd Surge Detected",
        "description": "Crowd density exceeded 85% at a venue gate",
        "enabled": True,
        "source": "Rest API",
        "executionSettings": {},
        "analyzer": {
            "name": "davis.static.threshold",
            "input": [
                {"key": "metricSelector", "value": "worldcup.crowd.density:max"},
                {"key": "threshold", "value": "85"},
                {"key": "violatingSamples", "value": "1"},
                {"key": "samples", "value": "3"},
                {"key": "dealertingSamples", "value": "3"},
                {"key": "alertCondition", "value": "ABOVE"}
            ]
        },
        "eventTemplate": {
            "properties": [
                {"key": "severity", "value": "HIGH"},
                {"key": "type", "value": "CROWD_SURGE"}
            ]
        }
    },
    {
        "title": "Infrastructure CPU Critical",
        "description": "Venue infrastructure CPU exceeded 85%",
        "enabled": True,
        "source": "Rest API",
        "executionSettings": {},
        "analyzer": {
            "name": "davis.static.threshold",
            "input": [
                {"key": "metricSelector", "value": "worldcup.infra.cpu:max"},
                {"key": "threshold", "value": "85"},
                {"key": "violatingSamples", "value": "1"},
                {"key": "samples", "value": "3"},
                {"key": "dealertingSamples", "value": "3"},
                {"key": "alertCondition", "value": "ABOVE"}
            ]
        },
        "eventTemplate": {
            "properties": [
                {"key": "severity", "value": "HIGH"},
                {"key": "type", "value": "INFRA_SPIKE"}
            ]
        }
    }
]

for alert in alerts:
    payload = [
        {
            "schemaId": "builtin:davis.anomaly-detectors",
            "scope": "environment",
            "value": alert
        }
    ]
    response = requests.post(
        f"{DT_URL}/api/v2/settings/objects",
        headers=headers,
        json=payload
    )
    if response.status_code in [200, 201]:
        print(f"✅ Alert created: {alert['title']}")
    else:
        print(f"❌ Failed: {alert['title']} → {response.status_code}: {response.text}")
