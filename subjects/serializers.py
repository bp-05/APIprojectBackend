from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .models import (
    Subject,
    Area,
    Career,
    SemesterLevel,
    SubjectUnit,
    SubjectTechnicalCompetency,
    CompanyBoundaryCondition,
    PossibleCounterpart,
    InteractionType,
    Api3Alternance,
    ApiType2Completion,
    ApiType3Completion,
    PeriodPhaseSchedule,
)
"""Serializers for subjects app.

ProblemStatement and CounterpartContact serializers were moved to companies.serializers
"""


class SubjectSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)
    career_name = serializers.CharField(source='career.name', read_only=True)
    semester_name = serializers.CharField(source='semester.name', read_only=True)
    period_code = serializers.CharField(read_only=True)
    phase_start_date = serializers.DateField(read_only=True)
    phase_end_date = serializers.DateField(read_only=True)
    process_start_date = serializers.DateField(read_only=True)
    process_end_date = serializers.DateField(read_only=True)

    class Meta:
        model = Subject
        fields = [
            'id',
            'code',
            'section',
            'name',
            'campus',
            'shift',
            'period_year',
            'period_season',
            'period_code',
            'phase',
            'phase_start_date',
            'phase_end_date',
            'process_start_date',
            'process_end_date',
            'hours',
            'api_type',
            'teacher',
            'teacher_name',
            'area',
            'area_name',
            'career',
            'career_name',
            'semester',
            'semester_name',
        ]
        extra_kwargs = {
            'teacher': {'required': False, 'allow_null': True},
        }
        validators = [
            UniqueTogetherValidator(
                queryset=Subject.objects.all(),
                fields=['code', 'section', 'period_year', 'period_season'],
                message='code, section y periodo deben ser únicos en conjunto'
            )
        ]

    def validate_teacher(self, value):
        if value is None:
            return value
        if getattr(value, 'role', None) != 'DOC':
            raise serializers.ValidationError('teacher debe ser un usuario con rol DOC')
        return value


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ['id', 'name']


class CareerSerializer(serializers.ModelSerializer):
    area_name = serializers.CharField(source='area.name', read_only=True)

    class Meta:
        model = Career
        fields = ['id', 'name', 'area', 'area_name']


class SemesterLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SemesterLevel
        fields = ['id', 'name']


class SubjectUnitSerializer(serializers.ModelSerializer):
    number = serializers.IntegerField(min_value=1, max_value=4)
    unit_hours = serializers.IntegerField(min_value=0, required=False, allow_null=True)

    class Meta:
        model = SubjectUnit
        fields = [
            'id', 'subject', 'number', 'expected_learning', 'unit_hours', 'activities_description',
            'evaluation_evidence', 'evidence_detail', 'counterpart_link', 'place_mode_type',
            'counterpart_participant_name'
        ]
        validators = [
            UniqueTogetherValidator(
                queryset=SubjectUnit.objects.all(),
                fields=['subject', 'number'],
                message='number debe ser único por asignatura'
            )
        ]


class SubjectTechnicalCompetencySerializer(serializers.ModelSerializer):
    number = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = SubjectTechnicalCompetency
        fields = ['id', 'subject', 'number', 'description']
        validators = [
            UniqueTogetherValidator(
                queryset=SubjectTechnicalCompetency.objects.all(),
                fields=['subject', 'number'],
                message='number de la competencia debe ser único por asignatura'
            )
        ]


class CompanyBoundaryConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyBoundaryCondition
        fields = [
            'id', 'subject', 'large_company', 'medium_company', 'small_company', 'family_enterprise',
            'not_relevant', 'company_type_description', 'company_requirements_for_level_2_3', 'project_minimum_elements'
        ]

    def validate(self, attrs):
        subject = attrs.get('subject') or getattr(self.instance, 'subject', None)
        if subject is not None:
            qs = CompanyBoundaryCondition.objects.filter(subject=subject)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({'subject': 'Ya existe una condición de borde para esta asignatura'})
        return super().validate(attrs)


class PossibleCounterpartSerializer(serializers.ModelSerializer):
    # Exponer como lista de códigos usando el m2m 'interaction_types'
    interaction_type = serializers.SlugRelatedField(
        many=True,
        source='interaction_types',
        slug_field='code',
        queryset=InteractionType.objects.all(),
        required=False,
    )

    class Meta:
        model = PossibleCounterpart
        fields = [
            'id',
            'sector',
            'worked_before',
            'interest_collaborate',
            'can_develop_activities',
            'willing_design_project',
            'interaction_type',
            'has_guide',
            'can_receive_alternance',
            'alternance_students_quota',
            'subject',
            'company',
        ]
        extra_kwargs = {
            'subject': {'allow_null': True, 'required': False},
        }

    # No es necesario sobreescribir create/update: DRF maneja m2m con SlugRelatedField


class Api3AlternanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Api3Alternance
        fields = [
            'id',
            'student_role',
            'students_quota',
            'tutor_name',
            'tutor_email',
            'alternance_hours',
            'subject',
        ]


class ApiType2CompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiType2Completion
        fields = [
            'id',
            'project_goal_students',
            'deliverables_at_end',
            'company_expected_participation',
            'other_activities',
            'subject',
        ]


class ApiType3CompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiType3Completion
        fields = [
            'id',
            'project_goal_students',
            'deliverables_at_end',
            'expected_student_role',
            'other_activities',
            'master_guide_expected_support',
            'subject',
        ]


## ProblemStatement serializers moved to companies.serializers


class PeriodPhaseScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodPhaseSchedule
        fields = [
            'id',
            'period_year',
            'period_season',
            'phase',
            'days_allocated',
            'start_date',
            'end_date',
        ]

    def validate(self, attrs):
        start = attrs.get('start_date')
        end = attrs.get('end_date')
        if start and end and end < start:
            raise serializers.ValidationError({'end_date': 'end_date no puede ser anterior a start_date'})
        return attrs
