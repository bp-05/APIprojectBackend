from django.shortcuts import render
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from .serializers import UserMeSerializer, UserListSerializer, PasswordChangeSerializer
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

    # Create your views here.
