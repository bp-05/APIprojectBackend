from django.shortcuts import render
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from .serializers import UserMeSerializer, UserListSerializer
from .permissions import IsAdminOrReadOnly

User = get_user_model()

class MeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Endpoint /api/users/me/ que retorna el usuario autenticado."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserMeSerializer

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class UserViewSet(viewsets.ModelViewSet):
    """CRUD de usuarios (solo Admin escribe)."""
    queryset = User.objects.all().order_by('id')
    serializer_class = UserListSerializer
    permission_classes = [IsAdminOrReadOnly]

    filterset_fields = ['role','is_active','is_staff']
    search_fields = ['username','email','first_name','last_name']
    ordering_fields = ['id','username','date_joined']

# Create your views here.
