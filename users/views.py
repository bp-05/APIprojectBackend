from django.shortcuts import render
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from .serializers import (
    UserMeSerializer,
    UserListSerializer,
    UserCreateSerializer,
    PasswordChangeSerializer,
    UserAdminUpdateSerializer,
)
from .permissions import IsAdminOrReadOnly

User = get_user_model()


class MeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Endpoint /api/users/me/ que retorna y permite acciones sobre el usuario autenticado."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserMeSerializer

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(methods=['post'], detail=False, url_path='change-password')
    def change_password(self, request, *args, **kwargs):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"detail": "Contraseña actualizada correctamente"}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """CRUD de usuarios (solo Admin escribe)."""
    queryset = User.objects.all().order_by('id')
    serializer_class = UserListSerializer
    permission_classes = [IsAdminOrReadOnly]

    filterset_fields = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['id', 'email', 'date_joined']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ('update', 'partial_update'):
            return UserAdminUpdateSerializer
        return super().get_serializer_class()

    # Create your views here.

    @action(methods=['get'], detail=False, url_path='teachers', permission_classes=[IsAuthenticated])
    def list_teachers(self, request, *args, **kwargs):
        user = request.user
        is_vcm = user.groups.filter(name__in=['vcm']).exists()
        if not (getattr(user, 'is_staff', False) or getattr(user, 'role', None) in ['ADMIN', 'DAC'] or is_vcm):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        qs = User.objects.filter(role='DOC', is_active=True).order_by('first_name', 'last_name', 'email')
        serializer = UserListSerializer(qs, many=True)
        return Response(serializer.data)
