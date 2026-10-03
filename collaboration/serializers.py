from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import (
    Workspace,
    WorkspaceMember,
    WorkspaceInvitation,
)

User = get_user_model()


class WorkspaceMemberSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    email = serializers.EmailField(
        source="user.email",
        read_only=True
    )

    class Meta:

        model = WorkspaceMember

        fields = [
            "id",
            "username",
            "email",
            "role",
            "joined_at",
        ]


class WorkspaceSerializer(serializers.ModelSerializer):

    owner = serializers.CharField(
        source="owner.username",
        read_only=True
    )

    members_count = serializers.SerializerMethodField()

    class Meta:

        model = Workspace

        fields = [
            "id",
            "name",
            "description",
            "owner",
            "is_personal",
            "members_count",
            "created_at",
            "updated_at",
        ]

    def get_members_count(self, obj):
        return obj.members.count()


class WorkspaceCreateSerializer(serializers.ModelSerializer):

    class Meta:

        model = Workspace

        fields = [
            "name",
            "description",
        ]

    def create(self, validated_data):

        request = self.context["request"]

        workspace = Workspace.objects.create(
            owner=request.user,
            **validated_data
        )

        WorkspaceMember.objects.create(
            workspace=workspace,
            user=request.user,
            role=WorkspaceMember.ROLE_ADMIN,
        )

        return workspace


class WorkspaceInvitationSerializer(serializers.ModelSerializer):

    invited_by = serializers.CharField(
        source="invited_by.username",
        read_only=True
    )

    workspace = serializers.CharField(
        source="workspace.name",
        read_only=True
    )

    class Meta:

        model = WorkspaceInvitation

        fields = [
            "id",
            "workspace",
            "email",
            "status",
            "token",
            "invited_by",
            "expires_at",
            "created_at",
        ]


class InviteMemberSerializer(serializers.Serializer):

    email = serializers.EmailField()