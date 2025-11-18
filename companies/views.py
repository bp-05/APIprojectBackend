from rest_framework import viewsets, permissions
from rest_framework import exceptions
from django.db.models import Q
from subjects.models import Subject
from .models import Company, ProblemStatement, CompanyEngagementScope, CounterpartContact
from .serializers import (
    CompanySerializer,
    ProblemStatementSerializer,
    CompanyEngagementScopeSerializer,
    CounterpartContactSerializer,
)


def _has_full_company_scope(user):
    return (
        getattr(user, 'is_staff', False)
        or getattr(user, 'role', None) in ['VCM', 'COORD']
        or user.groups.filter(name__in=['vcm']).exists()
    )


def _director_problemstatement_scope(user):
    if getattr(user, 'role', None) != 'DC':
        return None
    career_id = getattr(user, 'career_id', None)
    if career_id:
        return Q(subject__career_id=career_id)
    area_id = getattr(user, 'area_id', None)
    if area_id:
        return Q(subject__area_id=area_id)
    return None


def _director_subject_queryset(user):
    if getattr(user, 'role', None) != 'DC':
        return Subject.objects.none()
    qs = Subject.objects.all()
    career_id = getattr(user, 'career_id', None)
    if career_id:
        return qs.filter(career_id=career_id)
    area_id = getattr(user, 'area_id', None)
    if area_id:
        return qs.filter(area_id=area_id)
    return Subject.objects.none()


def _subject_pairs_for_director(user):
    qs = _director_subject_queryset(user)
    return list(qs.values_list('code', 'section', 'period_year', 'period_season'))


def _accessible_company_ids(user):
    teacher_subject_ids = set(
        Subject.objects.filter(teacher=user).values_list('id', flat=True)
    )
    director_subject_ids = set(
        _director_subject_queryset(user).values_list('id', flat=True)
    )
    subject_ids = teacher_subject_ids | director_subject_ids
    if not subject_ids:
        return set()
    return set(
        ProblemStatement.objects.filter(subject_id__in=subject_ids)
        .values_list('company_id', flat=True)
    )


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
        if _has_full_company_scope(user):
            return qs
        director_scope = _director_problemstatement_scope(user)
        if director_scope is not None:
            return qs.filter(director_scope | Q(subject__teacher=user))
        return qs.filter(subject__teacher=user)


class CompanyEngagementScopeViewSet(viewsets.ModelViewSet):
    queryset = CompanyEngagementScope.objects.all().select_related('company')
    serializer_class = CompanyEngagementScopeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['company', 'subject_code', 'subject_section', 'subject_period_season', 'subject_period_year']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if _has_full_company_scope(user):
            return qs
        # Limitar por asignaturas del docente y directores sin FK: construir OR por code+section
        cond = Q(pk__isnull=True)
        teacher_pairs = Subject.objects.filter(teacher=user).values_list('code', 'section', 'period_year', 'period_season')
        for code, section, period_year, period_season in teacher_pairs:
            cond |= Q(
                subject_code=code,
                subject_section=section,
                subject_period_year=period_year,
                subject_period_season=period_season,
            )
        for code, section, period_year, period_season in _subject_pairs_for_director(user):
            cond |= Q(
                subject_code=code,
                subject_section=section,
                subject_period_year=period_year,
                subject_period_season=period_season,
            )
        return qs.filter(cond)


class CounterpartContactViewSet(viewsets.ModelViewSet):
    queryset = CounterpartContact.objects.all().select_related('company')
    serializer_class = CounterpartContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['company']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if _has_full_company_scope(user):
            return qs
        company_ids = _accessible_company_ids(user)
        if not company_ids:
            return qs.none()
        return qs.filter(company_id__in=company_ids)

    def _ensure_company_access(self, company):
        user = self.request.user
        if _has_full_company_scope(user):
            return
        if company.id not in _accessible_company_ids(user):
            raise exceptions.PermissionDenied('No autorizado para esta empresa.')

    def perform_create(self, serializer):
        company = serializer.validated_data.get('company')
        if not company:
            raise exceptions.ValidationError({'company': 'Campo requerido.'})
        self._ensure_company_access(company)
        serializer.save()

    def perform_update(self, serializer):
        company = serializer.validated_data.get('company', serializer.instance.company)
        self._ensure_company_access(company)
        serializer.save()

    def perform_destroy(self, instance):
        self._ensure_company_access(instance.company)
        super().perform_destroy(instance)
