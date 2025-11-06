from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, decorators, response, status
from .models import DescriptorFile
from .serializers import DescriptorUploadSerializer
from .tasks import process_descriptor

class DescriptorViewSet(viewsets.ModelViewSet):
    queryset = DescriptorFile.objects.all().select_related('subject')
    serializer_class = DescriptorUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'is_staff', False) or getattr(user, 'role', None) == 'DAC' or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(subject__teacher=user)

    def _has_elevated_access(self, user):
        return (
            getattr(user, 'is_staff', False)
            or getattr(user, 'role', None) in ['ADMIN', 'DAC']
            or user.groups.filter(name__in=['vcm']).exists()
        )

    def perform_create(self, serializer):
        user = self.request.user
        subject = serializer.validated_data.get('subject')
        if subject is not None and not (self._has_elevated_access(user) or subject.teacher_id == user.id):
            raise permissions.PermissionDenied('No puedes crear descriptores para esta asignatura')
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        subject = serializer.validated_data.get('subject', getattr(self.get_object(), 'subject', None))
        if subject is not None and not (self._has_elevated_access(user) or subject.teacher_id == user.id):
            raise permissions.PermissionDenied('No puedes actualizar descriptores para esta asignatura')
        serializer.save()

    @decorators.action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        descriptor = self.get_object()
        process_descriptor.delay(descriptor.id)  # tarea asíncrona
        return response.Response({"detail": "Procesamiento en curso."}, status=status.HTTP_202_ACCEPTED)
