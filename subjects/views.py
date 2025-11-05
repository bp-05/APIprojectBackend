from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    Subject,
    Area,
    SemesterLevel,
    SubjectUnit,
    SubjectTechnicalCompetency,
    CompanyBoundaryCondition,
    CompanyRequirement,
    Api3Alternance,
    ApiType2Completion,
    ApiType3Completion,
)
## ProblemStatement model imported by companies app where its views live
from .serializers import (
    SubjectSerializer,
    AreaSerializer,
    SemesterLevelSerializer,
    SubjectUnitSerializer,
    SubjectTechnicalCompetencySerializer,
    CompanyBoundaryConditionSerializer,
    CompanyRequirementSerializer,
    Api3AlternanceSerializer,
    ApiType2CompletionSerializer,
    ApiType3CompletionSerializer,
)
from .permissions import IsSubjectTeacherOrAdmin


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all().select_related('teacher', 'area')
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsSubjectTeacherOrAdmin]
    filterset_fields = ['code', 'section']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'is_staff', False ) or getattr(user, 'role', None) == 'DAC' or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(teacher=user)

    @action(detail=False, methods=['get'], url_path=r'by-code/(?P<code>[^/]+)/(?P<section>[^/]+)')
    def by_code(self, request, code=None, section=None):
        qs = self.get_queryset()
        try:
            obj = qs.get(code=code, section=section)
        except Subject.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path=r'code-sections')
    def code_sections(self, request):
        qs = self.get_queryset().order_by('code', 'section')
        data = [
            {
                'id': s.id,
                'code': s.code,
                'section': s.section,
                'name': s.name,
            }
            for s in qs
        ]
        return Response(data)


class AreaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Area.objects.all().order_by('name')
    serializer_class = AreaSerializer
    permission_classes = [permissions.IsAuthenticated]


class SubjectSemesterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SemesterLevel.objects.all().order_by('id')
    serializer_class = SemesterLevelSerializer
    permission_classes = [permissions.IsAuthenticated]


class SubjectUnitViewSet(viewsets.ModelViewSet):
    queryset = SubjectUnit.objects.all().select_related('subject')
    serializer_class = SubjectUnitSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['subject']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'is_staff', False ) or getattr(user, 'role', None) == 'DAC' or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(subject__teacher=user)


class SubjectTechnicalCompetencyViewSet(viewsets.ModelViewSet):
    queryset = SubjectTechnicalCompetency.objects.all().select_related('subject')
    serializer_class = SubjectTechnicalCompetencySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['subject']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'is_staff', False ) or getattr(user, 'role', None) == 'DAC' or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(subject__teacher=user)


class CompanyBoundaryConditionViewSet(viewsets.ModelViewSet):
    queryset = CompanyBoundaryCondition.objects.all().select_related('subject')
    serializer_class = CompanyBoundaryConditionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'is_staff', False ) or getattr(user, 'role', None) == 'DAC' or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(subject__teacher=user)


class CompanyRequirementViewSet(viewsets.ModelViewSet):
    queryset = CompanyRequirement.objects.all().select_related('subject', 'company')
    serializer_class = CompanyRequirementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'is_staff', False ) or getattr(user, 'role', None) == 'DAC' or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(subject__teacher=user)


class Api3AlternanceViewSet(viewsets.ModelViewSet):
    queryset = Api3Alternance.objects.all().select_related('subject')
    serializer_class = Api3AlternanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'is_staff', False ) or getattr(user, 'role', None) == 'DAC' or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(subject__teacher=user)


class ApiType2CompletionViewSet(viewsets.ModelViewSet):
    queryset = ApiType2Completion.objects.all().select_related('subject')
    serializer_class = ApiType2CompletionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'is_staff', False ) or getattr(user, 'role', None) == 'DAC' or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(subject__teacher=user)


class ApiType3CompletionViewSet(viewsets.ModelViewSet):
    queryset = ApiType3Completion.objects.all().select_related('subject')
    serializer_class = ApiType3CompletionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'is_staff', False ) or getattr(user, 'role', None) == 'DAC' or user.groups.filter(name__in=['vcm']).exists():
            return qs
        return qs.filter(subject__teacher=user)


## CompanyEngagementScopeViewSet movido a companies.views


## ProblemStatementViewSet movido a companies.views

