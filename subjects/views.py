from django.shortcuts import render

# Create your views here.
from django.db.models import Q
from django.http import HttpResponse, StreamingHttpResponse
from django.views.decorators.http import require_GET
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from .models import (
    Subject,
    Area,
    Career,
    SemesterLevel,
    SubjectUnit,
    SubjectTechnicalCompetency,
    CompanyBoundaryCondition,
    PossibleCounterpart,
    Api3Alternance,
    ApiType2Completion,
    ApiType3Completion,
    PeriodPhaseSchedule,
    CompanyEngagementScope,
    SubjectPhaseProgress,
)
## ProblemStatement model imported by companies app where its views live
from .serializers import (
    SubjectSerializer,
    AreaSerializer,
    CareerSerializer,
    SemesterLevelSerializer,
    SubjectUnitSerializer,
    SubjectTechnicalCompetencySerializer,
    CompanyBoundaryConditionSerializer,
    PossibleCounterpartSerializer,
    Api3AlternanceSerializer,
    ApiType2CompletionSerializer,
    ApiType3CompletionSerializer,
    PeriodPhaseScheduleSerializer,
    CompanyEngagementScopeSerializer,
    SubjectPhaseProgressSerializer,
)
from .permissions import IsSubjectTeacherOrAdmin, IsAdminOrCoordinator, IsAdminOrAcademicDept
from .utils import get_current_period, normalize_season_token, parse_period_string
from .events import subject_event_stream


def _authenticate_stream_request(request):
    """
    Resolve the authenticated user for the SSE endpoint using session or JWT.
    """
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        return user
    jwt_auth = JWTAuthentication()
    auth_header = request.META.get("HTTP_AUTHORIZATION")
    token_query = request.GET.get("token")
    if not auth_header and token_query:
        # Allow passing the JWT as a query param for EventSource compatibility
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {token_query}"
    try:
        authenticated = jwt_auth.authenticate(request)
    except (InvalidToken, Exception):
        authenticated = None
    if authenticated is None:
        return None
    return authenticated[0]


@require_GET
def subject_stream(request):
    user = _authenticate_stream_request(request)
    if not user:
        return HttpResponse(status=401)

    def event_generator():
        # Let the browser know how often to retry if the stream drops.
        yield "retry: 10000\n\n"
        with subject_event_stream() as listener:
            for message in listener:
                if message.get("type") != "message":
                    continue
                data = message.get("data")
                if not data:
                    continue
                yield f"data: {data}\n\n"

    response = StreamingHttpResponse(event_generator(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


def _director_scope_q(user, subject_field='subject'):
    """Return a Q object restricting records to the director's area/career."""
    if getattr(user, 'role', None) != 'DC':
        return None
    prefix = f'{subject_field}__' if subject_field else ''
    career_id = getattr(user, 'career_id', None)
    if career_id:
        return Q(**{f'{prefix}career_id': career_id})
    area_id = getattr(user, 'area_id', None)
    if area_id:
        return Q(**{f'{prefix}area_id': area_id})
    return None


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all().select_related('teacher', 'area', 'career')
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsSubjectTeacherOrAdmin]
    filterset_fields = ['code', 'section', 'period_year', 'period_season']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if (
            getattr(user, 'is_staff', False)
            or getattr(user, 'role', None) in ['DAC', 'VCM', 'COORD']
            or user.groups.filter(name__in=['vcm']).exists()
        ):
            return qs
        director_scope = _director_scope_q(user, subject_field='')
        if director_scope is not None:
            return qs.filter(director_scope | Q(teacher=user))
        return qs.filter(teacher=user)

    @action(detail=False, methods=['get'], url_path=r'by-code/(?P<code>[^/]+)/(?P<section>[^/]+)')
    def by_code(self, request, code=None, section=None):
        qs = self.get_queryset().filter(code=code, section=section)
        if not qs.exists():
            return Response({'detail': 'Not found.'}, status=404)
        period_param = request.query_params.get('period')
        season = None
        year = None
        if period_param:
            season, year = parse_period_string(period_param)
            if not (season and year):
                return Response({'detail': 'period debe tener formato O-2025.'}, status=400)
        else:
            period_season = request.query_params.get('period_season')
            if period_season:
                normalized = normalize_season_token(period_season)
                if not normalized:
                    return Response({'detail': 'period_season debe ser O o P.'}, status=400)
                season = normalized
            period_year = request.query_params.get('period_year')
            if period_year:
                try:
                    year = int(period_year)
                except ValueError:
                    return Response({'detail': 'period_year debe ser numérico.'}, status=400)
        default_season, default_year = get_current_period()
        season = season or default_season
        year = year or default_year
        obj = qs.filter(period_year=year, period_season=season).first()
        if not obj:
            return Response({'detail': 'Not found.'}, status=404)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path=r'code-sections')
    def code_sections(self, request):
        qs = self.get_queryset().order_by('code', 'section', '-period_year', '-period_season')
        data = [
            {
                'id': s.id,
                'code': s.code,
                'section': s.section,
                'name': s.name,
                'period_year': s.period_year,
                'period_season': s.period_season,
                'period': s.period_code,
            }
            for s in qs
        ]
        return Response(data)


class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all().order_by('name')
    serializer_class = AreaSerializer
    permission_classes = [IsAdminOrAcademicDept]


class CareerViewSet(viewsets.ModelViewSet):
    queryset = Career.objects.all().select_related('area').order_by('name')
    serializer_class = CareerSerializer
    permission_classes = [IsAdminOrAcademicDept]
    filterset_fields = ['area']
    search_fields = ['name']
    ordering_fields = ['name', 'area', 'area__name']


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
        if (
            getattr(user, 'is_staff', False)
            or getattr(user, 'role', None) in ['DAC', 'VCM', 'COORD']
            or user.groups.filter(name__in=['vcm']).exists()
        ):
            return qs
        director_scope = _director_scope_q(user)
        if director_scope is not None:
            return qs.filter(director_scope | Q(subject__teacher=user))
        return qs.filter(subject__teacher=user)


class SubjectTechnicalCompetencyViewSet(viewsets.ModelViewSet):
    queryset = SubjectTechnicalCompetency.objects.all().select_related('subject')
    serializer_class = SubjectTechnicalCompetencySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['subject']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if (
            getattr(user, 'is_staff', False)
            or getattr(user, 'role', None) in ['DAC', 'VCM', 'COORD']
            or user.groups.filter(name__in=['vcm']).exists()
        ):
            return qs
        director_scope = _director_scope_q(user)
        if director_scope is not None:
            return qs.filter(director_scope | Q(subject__teacher=user))
        return qs.filter(subject__teacher=user)


class CompanyBoundaryConditionViewSet(viewsets.ModelViewSet):
    queryset = CompanyBoundaryCondition.objects.all().select_related('subject')
    serializer_class = CompanyBoundaryConditionSerializer
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
        director_scope = _director_scope_q(user)
        if director_scope is not None:
            return qs.filter(director_scope | Q(subject__teacher=user))
        return qs.filter(subject__teacher=user)


class PossibleCounterpartViewSet(viewsets.ModelViewSet):
    queryset = PossibleCounterpart.objects.all().select_related('subject', 'company')
    serializer_class = PossibleCounterpartSerializer
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
        director_scope = _director_scope_q(user)
        if director_scope is not None:
            return qs.filter(director_scope | Q(subject__teacher=user))
        return qs.filter(subject__teacher=user)


class Api3AlternanceViewSet(viewsets.ModelViewSet):
    queryset = Api3Alternance.objects.all().select_related('subject')
    serializer_class = Api3AlternanceSerializer
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
        director_scope = _director_scope_q(user)
        if director_scope is not None:
            return qs.filter(director_scope | Q(subject__teacher=user))
        return qs.filter(subject__teacher=user)


class ApiType2CompletionViewSet(viewsets.ModelViewSet):
    queryset = ApiType2Completion.objects.all().select_related('subject')
    serializer_class = ApiType2CompletionSerializer
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
        director_scope = _director_scope_q(user)
        if director_scope is not None:
            return qs.filter(director_scope | Q(subject__teacher=user))
        return qs.filter(subject__teacher=user)


class ApiType3CompletionViewSet(viewsets.ModelViewSet):
    queryset = ApiType3Completion.objects.all().select_related('subject')
    serializer_class = ApiType3CompletionSerializer
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
        director_scope = _director_scope_q(user)
        if director_scope is not None:
            return qs.filter(director_scope | Q(subject__teacher=user))
        return qs.filter(subject__teacher=user)


## ProblemStatementViewSet movido a companies.views


class CompanyEngagementScopeViewSet(viewsets.ModelViewSet):
    queryset = CompanyEngagementScope.objects.all().select_related('subject')
    serializer_class = CompanyEngagementScopeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['subject']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if (
            getattr(user, 'is_staff', False)
            or getattr(user, 'role', None) in ['DAC', 'VCM', 'COORD']
            or user.groups.filter(name__in=['vcm']).exists()
        ):
            return qs
        director_scope = _director_scope_q(user)
        if director_scope is not None:
            return qs.filter(director_scope | Q(subject__teacher=user))
        return qs.filter(subject__teacher=user)


class PeriodPhaseScheduleViewSet(viewsets.ModelViewSet):
    queryset = PeriodPhaseSchedule.objects.all().order_by('period_year', 'period_season', 'phase')
    serializer_class = PeriodPhaseScheduleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrCoordinator]
    filterset_fields = ['period_year', 'period_season', 'phase']


class SubjectPhaseProgressViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar el progreso de fases de asignaturas (usado en vista Gantt).
    
    Solo ADMIN y COORD pueden modificar registros.
    Permite filtrar por subject para obtener el progreso de una asignatura específica.
    """
    queryset = SubjectPhaseProgress.objects.all().select_related('subject', 'updated_by')
    serializer_class = SubjectPhaseProgressSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrCoordinator]
    filterset_fields = ['subject', 'phase', 'status']

    def get_queryset(self):
        qs = super().get_queryset()
        # Filtro adicional por subject_id en query params
        subject_id = self.request.query_params.get('subject')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        return qs

    @action(detail=False, methods=['get'], url_path=r'by-subject/(?P<subject_id>\d+)')
    def by_subject(self, request, subject_id=None):
        """Obtiene todos los registros de progreso para una asignatura específica."""
        qs = self.get_queryset().filter(subject_id=subject_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='bulk-upsert')
    def bulk_upsert(self, request):
        """Crea o actualiza múltiples registros de progreso en una sola petición.
        
        Espera un array de objetos con: subject, phase, status, notes (opcional)
        """
        data_list = request.data if isinstance(request.data, list) else [request.data]
        results = []
        errors = []
        
        for item in data_list:
            subject_id = item.get('subject')
            phase = item.get('phase')
            status = item.get('status', 'nr')
            notes = item.get('notes', '')
            
            if not subject_id or not phase:
                errors.append({'error': 'subject y phase son requeridos', 'item': item})
                continue
            
            try:
                obj, created = SubjectPhaseProgress.objects.update_or_create(
                    subject_id=subject_id,
                    phase=phase,
                    defaults={
                        'status': status,
                        'notes': notes,
                        'updated_by': request.user,
                    }
                )
                serializer = self.get_serializer(obj)
                results.append({'created': created, 'data': serializer.data})
            except Exception as e:
                errors.append({'error': str(e), 'item': item})
        
        return Response({
            'success': results,
            'errors': errors,
        }, status=200 if not errors else 207)

