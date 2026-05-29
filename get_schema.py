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

response = requests.get(
    f"{DT_URL}/api/v2/settings/schemas/builtin:davis.anomaly-detectors",
    headers=headers
)

import json
print(json.dumps(response.json(), indent=2))
