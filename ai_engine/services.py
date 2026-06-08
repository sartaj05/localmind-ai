import requests
from django.conf import settings


def ask_local_model(prompt: str, model: str | None = None) -> str:
    """
    Sends user prompt to local Ollama model and returns AI response.
    """

    if not prompt:
        raise ValueError("Prompt is required")

    selected_model = model or settings.DEFAULT_AI_MODEL

    url = f"{settings.OLLAMA_BASE_URL}/api/generate"

    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
    }

    response = requests.post(url, json=payload, timeout=120)

    if response.status_code != 200:
        raise Exception(f"Ollama API error: {response.text}")

    data = response.json()
    return data.get("response", "")