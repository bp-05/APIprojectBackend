from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
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
"""Serializers for subjects app.

ProblemStatement and CounterpartContact serializers were moved to companies.serializers
"""


class SubjectSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)
    semester_name = serializers.CharField(source='semester.name', read_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'code', 'section', 'name', 'campus', 'hours', 'api_type', 'teacher', 'teacher_name', 'area', 'area_name', 'semester', 'semester_name']
        extra_kwargs = {
            'teacher': {'required': False, 'allow_null': True},
        }
        validators = [
            UniqueTogetherValidator(
                queryset=Subject.objects.all(),
                fields=['code', 'section'],
                message='code y section deben ser únicos en conjunto'
            )
        ]


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ['id', 'name']


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


class CompanyRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyRequirement
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
