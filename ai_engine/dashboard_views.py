from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import AIUsageLog, DailyAIUsage


class DashboardDailyRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        start_date = today - timedelta(days=6)

        usage_rows = DailyAIUsage.objects.filter(
            user=request.user,
            date__gte=start_date,
            date__lte=today,
        )

        usage_map = {
            row.date.isoformat(): row.request_count
            for row in usage_rows
        }

        results = []

        for index in range(7):
            current_date = start_date + timedelta(days=index)

            results.append(
                {
                    "date": current_date.isoformat(),
                    "requests": usage_map.get(current_date.isoformat(), 0),
                }
            )

        return Response(
            {
                "success": True,
                "results": results,
            }
        )


class DashboardModelUsageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = (
            AIUsageLog.objects.filter(user=request.user)
            .exclude(model_name="")
            .values("model_name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        results = [
            {
                "model": row["model_name"],
                "count": row["count"],
            }
            for row in rows
        ]

        return Response(
            {
                "success": True,
                "results": results,
            }
        )


class DashboardSuccessRateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        success_count = AIUsageLog.objects.filter(
            user=request.user,
            success=True,
        ).count()

        failed_count = AIUsageLog.objects.filter(
            user=request.user,
            success=False,
        ).count()

        return Response(
            {
                "success": True,
                "results": [
                    {
                        "name": "Success",
                        "value": success_count,
                    },
                    {
                        "name": "Failed",
                        "value": failed_count,
                    },
                ],
            }
        )