from django.shortcuts import render

# Create your views here.
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Workspace,
    WorkspaceMember,
    WorkspaceInvitation,
)

from .serializers import (
    WorkspaceSerializer,
    WorkspaceCreateSerializer,
    WorkspaceMemberSerializer,
    WorkspaceInvitationSerializer,
    InviteMemberSerializer,
)

User = get_user_model()

class WorkspaceListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        workspaces = Workspace.objects.filter(
            members__user=request.user
        ).distinct()

        serializer = WorkspaceSerializer(
            workspaces,
            many=True,
        )

        return Response(
            {
                "success": True,
                "results": serializer.data,
            }
        )

    def post(self, request):
        serializer = WorkspaceCreateSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        workspace = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Workspace created successfully.",
                "result": WorkspaceSerializer(workspace).data,
            },
            status=status.HTTP_201_CREATED,
        )
        
class WorkspaceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        workspace = get_object_or_404(
            Workspace,
            pk=pk,
        )

        if not WorkspaceMember.objects.filter(
            workspace=workspace,
            user=user,
        ).exists():
            return None

        return workspace

    def get(self, request, pk):
        workspace = self.get_object(pk, request.user)

        if workspace is None:
            return Response(
                {
                    "success": False,
                    "message": "Workspace not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = WorkspaceSerializer(workspace)

        return Response(
            {
                "success": True,
                "result": serializer.data,
            }
        )

    def patch(self, request, pk):
        workspace = self.get_object(pk, request.user)

        if workspace is None:
            return Response(
                {
                    "success": False,
                    "message": "Workspace not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        member = WorkspaceMember.objects.get(
            workspace=workspace,
            user=request.user,
        )

        if member.role != WorkspaceMember.ROLE_ADMIN:
            return Response(
                {
                    "success": False,
                    "message": "Only admin can update workspace.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = WorkspaceCreateSerializer(
            workspace,
            data=request.data,
            partial=True,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "success": True,
                "message": "Workspace updated.",
                "result": WorkspaceSerializer(workspace).data,
            }
        )

    def delete(self, request, pk):
        workspace = self.get_object(pk, request.user)

        if workspace is None:
            return Response(
                {
                    "success": False,
                    "message": "Workspace not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if workspace.owner != request.user:
            return Response(
                {
                    "success": False,
                    "message": "Only owner can delete workspace.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        workspace.delete()

        return Response(
            {
                "success": True,
                "message": "Workspace deleted.",
            }
        )
        
        