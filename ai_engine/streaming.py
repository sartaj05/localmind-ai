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

    if response.status_code != 200:
        yield f"\n[ERROR] Ollama API error: {response.text}"
        return

    for line in response.iter_lines():
        if not line:
            continue

        data = json.loads(line.decode("utf-8"))
        token = data.get("response", "")

        if token:
            yield token