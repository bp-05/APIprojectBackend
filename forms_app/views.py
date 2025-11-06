from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, decorators, response, status
from django.shortcuts import get_object_or_404
from .models import FormTemplate, FormInstance
from .serializers import FormTemplateSerializer, FormInstanceSerializer
from .permissions import IsFormOwnerOrCoordinator

class FormTemplateViewSet(viewsets.ModelViewSet):
    queryset = FormTemplate.objects.all()
    serializer_class = FormTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

class FormInstanceViewSet(viewsets.ModelViewSet):
    queryset = FormInstance.objects.select_related('subject','template')
    serializer_class = FormInstanceSerializer
    permission_classes = [permissions.IsAuthenticated, IsFormOwnerOrCoordinator]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        subject = self.request.query_params.get('subject')
        template = self.request.query_params.get('template')
        if subject:
            qs = qs.filter(subject__code=subject)
        if template:
            qs = qs.filter(template__key=template)
        if getattr(user, 'is_staff', False) or getattr(user, 'role', None) == 'VCM' or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(subject__teacher=user)

    @decorators.action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        obj = self.get_object()
        if obj.status == 'approved':
            return response.Response({'detail': 'Ya aprobado.'}, status=400)
        obj.status = 'in_review'
        obj.save(update_fields=['status'])
        return response.Response({'detail': 'Enviado a revisión.'})

    @decorators.action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        if not (request.user.is_staff or getattr(request.user, 'role', None) == 'VCM' or request.user.groups.filter(name__in=['vcm']).exists()):
            return response.Response({'detail': 'No autorizado.'}, status=403)
        obj = self.get_object()
        obj.status = 'approved'
        obj.save(update_fields=['status'])
        return response.Response({'detail': 'Aprobado.'})
