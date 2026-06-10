from datetime import date

from rest_framework.response import Response
from rest_framework import status

from .models import DailyAIUsage, UserAIPreference


def error_response(message, status_code=status.HTTP_400_BAD_REQUEST, errors=None):
    data = {
        "success": False,
        "error": {
            "message": message,
            "code": status_code,
        },
    }

    if errors is not None:
        data["error"]["details"] = errors

    return Response(data, status=status_code)


def success_response(data=None, message="", status_code=status.HTTP_200_OK):
    response_data = {
        "success": True,
    }

    if message:
        response_data["message"] = message

    if data is not None:
        response_data.update(data)

    return Response(response_data, status=status_code)


def estimate_text_usage(text):
    characters = len(text or "")
    estimated_tokens = max(1, characters // 4)

    return {
        "characters": characters,
        "estimated_tokens": estimated_tokens,
    }


def get_user_ai_preference(user):
    preference, _ = UserAIPreference.objects.get_or_create(user=user)
    return preference


def check_daily_quota(user, prompt_text):
    preference = get_user_ai_preference(user)
    usage, _ = DailyAIUsage.objects.get_or_create(
        user=user,
        date=date.today(),
    )

    text_usage = estimate_text_usage(prompt_text)

    if text_usage["characters"] > preference.max_prompt_characters:
        return False, {
            "reason": "Prompt is too large",
            "max_prompt_characters": preference.max_prompt_characters,
            "current_characters": text_usage["characters"],
        }

    if usage.request_count >= preference.daily_request_limit:
        return False, {
            "reason": "Daily AI request limit reached",
            "daily_request_limit": preference.daily_request_limit,
            "used_today": usage.request_count,
        }

    return True, {
        "usage": usage,
        "text_usage": text_usage,
    }


def increase_daily_usage(user, prompt_text):
    usage, _ = DailyAIUsage.objects.get_or_create(
        user=user,
        date=date.today(),
    )

    text_usage = estimate_text_usage(prompt_text)

    usage.request_count += 1
    usage.character_count += text_usage["characters"]
    usage.save(update_fields=["request_count", "character_count"])

    return usage