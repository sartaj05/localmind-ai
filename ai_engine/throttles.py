from rest_framework.throttling import UserRateThrottle


class AIUserRateThrottle(UserRateThrottle):
    scope = "ai_user"