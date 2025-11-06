from django.shortcuts import render
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError

from .serializers import (
    UserMeSerializer,
    UserListSerializer,
    UserCreateSerializer,
    PasswordChangeSerializer,
    UserAdminUpdateSerializer,
    TeacherManageSerializer,
)
from .permissions import IsAdminOrReadOnly, IsAdminOrDAC

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
        is_vcm_group = user.groups.filter(name__in=['vcm']).exists()
        is_vcm_role = getattr(user, 'role', None) == 'VCM'
        if not (getattr(user, 'is_staff', False) or getattr(user, 'role', None) in ['ADMIN', 'DAC'] or is_vcm_group or is_vcm_role):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        qs = User.objects.filter(role='DOC', is_active=True).order_by('first_name', 'last_name', 'email')
        serializer = UserListSerializer(qs, many=True)
        return Response(serializer.data)


class TeachersViewSet(viewsets.ModelViewSet):
    """CRUD de docentes (role='DOC') gestionado por ADMIN o DAC.

    - Lista y detalle disponibles para usuarios autenticados.
    - Escritura (create/update/delete) restringida a ADMIN o DAC.
    - En create/update se fuerza role='DOC' y se limitan campos.
    """
    queryset = User.objects.filter(role='DOC').order_by('first_name', 'last_name', 'email')
    permission_classes = [IsAuthenticated, IsAdminOrDAC]

    def get_serializer_class(self):
        # Para lectura simple podemos reutilizar UserListSerializer
        if self.action in ('list', 'retrieve'):
            return UserListSerializer
        return TeacherManageSerializer

    def perform_create(self, serializer):
        # Fuerza role='DOC' aunque no venga en payload
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def get_queryset(self):
        # Asegura filtrar por rol DOC siempre
        return super().get_queryset().filter(role='DOC')

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response({
                'detail': 'No se puede eliminar el docente porque tiene asignaturas asociadas. Reasigna o elimina las referencias primero.'
            }, status=status.HTTP_409_CONFLICT)
