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
        if getattr(user, 'is_staff', False) or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(subject__teacher=user)

    @decorators.action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        descriptor = self.get_object()
        process_descriptor.delay(descriptor.id)  # tarea asíncrona
        return response.Response({"detail": "Procesamiento en curso."}, status=status.HTTP_202_ACCEPTED)
