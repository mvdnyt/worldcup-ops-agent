import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    vertexai=True,
    project=os.getenv("GCP_PROJECT_ID"),
    location="us-central1"
)

for model in client.models.list():
    print(model.name)
