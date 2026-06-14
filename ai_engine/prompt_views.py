from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import PromptTemplate
from .prompt_serializers import (
    PromptTemplateSerializer,
    PromptTemplateCreateUpdateSerializer,
)


class PromptTemplateListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = request.query_params.get("search", "")
        category = request.query_params.get("category", "")

        prompts = PromptTemplate.objects.filter(user=request.user)

        if search:
            prompts = prompts.filter(title__icontains=search)

        if category:
            prompts = prompts.filter(category=category)

        serializer = PromptTemplateSerializer(prompts, many=True)

        return Response(
            {
                "success": True,
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = PromptTemplateCreateUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        prompt = PromptTemplate.objects.create(
            user=request.user,
            title=serializer.validated_data["title"],
            category=serializer.validated_data.get("category", "other"),
            prompt=serializer.validated_data["prompt"],
            is_pinned=serializer.validated_data.get("is_pinned", False),
        )

        return Response(
            {
                "success": True,
                "message": "Prompt template created successfully",
                "result": PromptTemplateSerializer(prompt).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PromptTemplateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return PromptTemplate.objects.get(pk=pk, user=request.user)
        except PromptTemplate.DoesNotExist:
            return None

    def get(self, request, pk):
        prompt = self.get_object(request, pk)

        if prompt is None:
            return Response(
                {
                    "success": False,
                    "error": "Prompt template not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "success": True,
                "result": PromptTemplateSerializer(prompt).data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        prompt = self.get_object(request, pk)

        if prompt is None:
            return Response(
                {
                    "success": False,
                    "error": "Prompt template not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PromptTemplateCreateUpdateSerializer(
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        for field, value in serializer.validated_data.items():
            setattr(prompt, field, value)

        prompt.save()

        return Response(
            {
                "success": True,
                "message": "Prompt template updated successfully",
                "result": PromptTemplateSerializer(prompt).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        prompt = self.get_object(request, pk)

        if prompt is None:
            return Response(
                {
                    "success": False,
                    "error": "Prompt template not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        prompt.delete()

        return Response(
            {
                "success": True,
                "message": "Prompt template deleted successfully",
            },
            status=status.HTTP_200_OK,
        )


class TogglePinPromptTemplateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        prompt = PromptTemplate.objects.filter(
            pk=pk,
            user=request.user,
        ).first()

        if prompt is None:
            return Response(
                {
                    "success": False,
                    "error": "Prompt template not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        prompt.is_pinned = not prompt.is_pinned
        prompt.save(update_fields=["is_pinned", "updated_at"])

        return Response(
            {
                "success": True,
                "message": "Prompt pin updated successfully",
                "result": PromptTemplateSerializer(prompt).data,
            },
            status=status.HTTP_200_OK,
        )