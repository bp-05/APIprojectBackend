from rest_framework import viewsets, permissions
from django.db.models import Q
from .models import Company, ProblemStatement, CompanyEngagementScope
from .serializers import CompanySerializer, ProblemStatementSerializer, CompanyEngagementScopeSerializer


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all().order_by('name')
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]


class ProblemStatementViewSet(viewsets.ModelViewSet):
    queryset = ProblemStatement.objects.all().select_related('subject', 'company')
    serializer_class = ProblemStatementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if (
            getattr(user, 'is_staff', False)
            or getattr(user, 'role', None) in ['VCM', 'COORD']
            or user.groups.filter(name__in=['vcm']).exists()
        ):
            return qs
        return qs.filter(subject__teacher=user)


class CompanyEngagementScopeViewSet(viewsets.ModelViewSet):
    queryset = CompanyEngagementScope.objects.all().select_related('company')
    serializer_class = CompanyEngagementScopeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['company', 'subject_code', 'subject_section']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if (
            getattr(user, 'is_staff', False)
            or getattr(user, 'role', None) in ['VCM', 'COORD']
            or user.groups.filter(name__in=['vcm']).exists()
        ):
            return qs
        # Limitar por asignaturas del docente sin FK: construir OR por code+section
        from subjects.models import Subject
        pairs = Subject.objects.filter(teacher=user).values_list('code', 'section')
        cond = Q(pk__isnull=True)
        for code, section in pairs:
            cond = cond | (Q(subject_code=code) & Q(subject_section=section))
        return qs.filter(cond)
