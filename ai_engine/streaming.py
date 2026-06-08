import json
import requests
from django.conf import settings


def stream_ollama_response(prompt, model=None):
    selected_model = model or settings.DEFAULT_AI_MODEL

    url = f"{settings.OLLAMA_BASE_URL}/api/generate"

    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": True,
    }

    response = requests.post(
        url,
        json=payload,
        stream=True,
        timeout=300,
    )

    for line in response.iter_lines():

        if not line:
            continue

        data = json.loads(line)

        token = data.get("response", "")

        yield token