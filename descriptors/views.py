from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, decorators, response, status, serializers
from .models import DescriptorFile
from .serializers import DescriptorUploadSerializer
from .strict_tasks import process_descriptor_strict
from .utils_descriptor_validation import _norm_code, extract_code_from_path_robust

class DescriptorViewSet(viewsets.ModelViewSet):
    queryset = DescriptorFile.objects.all().select_related('subject')
    serializer_class = DescriptorUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if (
            getattr(user, 'is_staff', False)
            or getattr(user, 'role', None) in ['DAC', 'VCM', 'COORD']
            or user.groups.filter(name__in=['vcm']).exists()
        ):
            return qs
        return qs.filter(subject__teacher=user)

    def _has_elevated_access(self, user):
        return (
            getattr(user, 'is_staff', False)
            or getattr(user, 'role', None) in ['ADMIN', 'DAC', 'VCM']
            or user.groups.filter(name__in=['vcm']).exists()
        )

    def perform_create(self, serializer):
        user = self.request.user
        subject = serializer.validated_data.get('subject')
        if subject is not None and not (self._has_elevated_access(user) or subject.teacher_id == user.id):
            raise permissions.PermissionDenied('No puedes crear descriptores para esta asignatura')
        instance = serializer.save()
        file_obj = getattr(instance, 'file', None)
        file_path = getattr(file_obj, 'path', None)
        file_name = getattr(file_obj, 'name', None)
        if subject is not None and file_path:
            code = extract_code_from_path_robust(
                file_path,
                subject_name=getattr(subject, 'name', None),
                file_name=file_name,
            )
            exp = _norm_code(getattr(subject, 'code', None))
            if not code or (exp and code != exp):
                instance.delete()
                if not code:
                    raise serializers.ValidationError({'file': 'no es posible extraer el codigo de asignatura del pdf'})
                raise serializers.ValidationError({'file': 'el descriptor no corresponde a la asignatura'})

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        subject = serializer.validated_data.get('subject', getattr(instance, 'subject', None))
        if subject is not None and not (self._has_elevated_access(user) or subject.teacher_id == user.id):
            raise permissions.PermissionDenied('No puedes actualizar descriptores para esta asignatura')
        instance = serializer.save()
        file_obj = getattr(instance, 'file', None)
        file_path = getattr(file_obj, 'path', None)
        file_name = getattr(file_obj, 'name', None)
        if subject is not None and file_path:
            code = extract_code_from_path_robust(
                file_path,
                subject_name=getattr(subject, 'name', None),
                file_name=file_name,
            )
            exp = _norm_code(getattr(subject, 'code', None))
            if not code:
                raise serializers.ValidationError({'file': 'no es posible extraer el codigo de asignatura del pdf'})
            if exp and code != exp:
                raise serializers.ValidationError({'file': 'el descriptor no corresponde a la asignatura'})

    @decorators.action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        descriptor = self.get_object()
        process_descriptor_strict.delay(descriptor.id)  # tarea asíncrona
        return response.Response({"detail": "Procesamiento en curso."}, status=status.HTTP_202_ACCEPTED)
