import requests
from django.conf import settings


def ask_local_model(prompt: str, model: str | None = None) -> str:
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


def build_context_prompt(messages, new_message: str, max_messages: int = 10) -> str:
    recent_messages = messages.order_by("-created_at")[:max_messages]
    recent_messages = reversed(list(recent_messages))

    conversation_text = ""

    for msg in recent_messages:
        if msg.role == "user":
            conversation_text += f"User: {msg.content}\n"
        else:
            conversation_text += f"Assistant: {msg.content}\n"

    final_prompt = f"""
You are a helpful AI assistant. Continue the conversation using the previous chat context.

Previous conversation:
{conversation_text}

New user message:
User: {new_message}

Assistant:
"""

    return final_prompt



def build_rag_context_prompt(messages, new_message: str, rag_context: str, max_messages: int = 8) -> str:
    recent_messages = messages.order_by("-created_at")[:max_messages]
    recent_messages = reversed(list(recent_messages))

    conversation_text = ""

    for msg in recent_messages:
        if msg.role == "user":
            conversation_text += f"User: {msg.content}\n"
        else:
            conversation_text += f"Assistant: {msg.content}\n"

    final_prompt = f"""
You are a helpful AI assistant.

Use the uploaded document context first.
Also use previous conversation only if it helps.

If the answer is not found in uploaded document context, say:
"I do not have enough information in the uploaded knowledge base."

Uploaded document context:
{rag_context}

Previous conversation:
{conversation_text}

New user message:
User: {new_message}

Assistant:
"""

    return final_prompt


def list_local_models():
    url = f"{settings.OLLAMA_BASE_URL}/api/tags"

    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        raise Exception(f"Ollama API error: {response.text}")

    data = response.json()

    models = []

    for item in data.get("models", []):
        models.append(
            {
                "name": item.get("name"),
                "size": item.get("size"),
                "modified_at": item.get("modified_at"),
            }
        )

    return models

def check_ollama_health():
    url = f"{settings.OLLAMA_BASE_URL}/api/tags"

    try:
        response = requests.get(url, timeout=10)

        return {
            "available": response.status_code == 200,
            "status_code": response.status_code,
        }

    except requests.RequestException as error:
        return {
            "available": False,
            "error": str(error),
        }
        
def generate_chat_title(user_message: str, model: str | None = None) -> str:
    prompt = f"""
Create a short chat title for this user message.

Rules:
- Maximum 5 words
- No quotes
- No full sentence
- Return only the title

User message:
{user_message}

Title:
"""

    title = ask_local_model(
        prompt=prompt,
        model=model,
    )

    title = title.strip().replace('"', "").replace("'", "")

    if not title:
        return user_message[:50]

    return title[:80]