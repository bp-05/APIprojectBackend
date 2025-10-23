from rest_framework import serializers
from .models import Subject, Area, SemesterLevel, CompanyRequirement, Api3Alternance, ApiType2Completion, ApiType3Completion, CompanyEngagementScope, ProblemStatement, default_subject_units, default_subject_competencies, default_company_boundary_conditions, default_counterpart_contacts


class SubjectUnitItemSerializer(serializers.Serializer):
    number = serializers.IntegerField(required=True, allow_null=True)
    expected_learning = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    unit_hours = serializers.IntegerField(required=True, allow_null=True, min_value=0)
    activities_description = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    evaluation_evidence = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    evidence_detail = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    counterpart_link = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    place_mode_type = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    counterpart_participant_name = serializers.CharField(required=True, allow_null=True, allow_blank=True)


class SubjectTechnicalCompetencyItemSerializer(serializers.Serializer):
    number = serializers.IntegerField(required=True)
    description = serializers.CharField(required=True, allow_blank=True, allow_null=True)


class CompanyBoundaryConditionsSerializer(serializers.Serializer):
    large_company = serializers.BooleanField(required=True)
    medium_company = serializers.BooleanField(required=True)
    small_company = serializers.BooleanField(required=True)
    family_enterprise = serializers.BooleanField(required=True)
    not_relevant = serializers.BooleanField(required=True)
    company_type_description = serializers.CharField(required=True, allow_blank=True, allow_null=True)
    company_requirements_for_level_2_3 = serializers.CharField(required=True, allow_blank=True, allow_null=True)
    project_minimum_elements = serializers.CharField(required=True, allow_blank=True, allow_null=True)

class SubjectSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True)
    semester_name = serializers.CharField(source='semester.name', read_only=True)
    units = SubjectUnitItemSerializer(many=True, required=False, default=default_subject_units)
    technical_competencies = SubjectTechnicalCompetencyItemSerializer(many=True, required=False, default=default_subject_competencies)
    company_boundary_conditions = CompanyBoundaryConditionsSerializer(required=False, default=default_company_boundary_conditions)

    class Meta:
        model = Subject
        fields = ['id', 'code', 'name', 'campus', 'hours', 'api_type', 'units', 'technical_competencies', 'company_boundary_conditions', 'teacher', 'teacher_name', 'area', 'area_name', 'semester', 'semester_name']
        extra_kwargs = {
            'teacher': {'required': False, 'allow_null': True},
        }

    def validate_units(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError('units must be a list')
        if len(value) > 4:
            raise serializers.ValidationError('units must have at most 4 items')
        numbers = []
        for item in value:
            n = item.get('number') if isinstance(item, dict) else None
            if n is not None:
                if not (1 <= n <= 4):
                    raise serializers.ValidationError('unit.number must be between 1 and 4')
                numbers.append(n)
        if len(numbers) != len(set(numbers)):
            raise serializers.ValidationError('unit.number values must be unique within units')
        return value

    def validate_technical_competencies(self, value):
        if value is None:
            return default_subject_competencies()
        if not isinstance(value, list):
            raise serializers.ValidationError('technical_competencies must be a list')
        if len(value) > 5:
            raise serializers.ValidationError('technical_competencies must have at most 5 items')
        numbers = []
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError('Each competency must be an object')
            n = item.get('number')
            if n is None:
                raise serializers.ValidationError('competency.number is required')
            if not (1 <= int(n) <= 5):
                raise serializers.ValidationError('competency.number must be between 1 and 5')
            numbers.append(int(n))
        if len(numbers) != len(set(numbers)):
            raise serializers.ValidationError('competency.number values must be unique within technical_competencies')
        return value

    def validate_company_boundary_conditions(self, value):
        if value is None:
            return default_company_boundary_conditions()
        if not isinstance(value, dict):
            raise serializers.ValidationError('company_boundary_conditions must be an object')
        required_keys = {
            'large_company',
            'medium_company',
            'small_company',
            'family_enterprise',
            'not_relevant',
            'company_type_description',
            'company_requirements_for_level_2_3',
            'project_minimum_elements',
        }
        missing = required_keys - set(value.keys())
        if missing:
            raise serializers.ValidationError(f'missing keys: {sorted(list(missing))}')
        # Basic type checks for booleans
        for k in ['large_company','medium_company','small_company','family_enterprise','not_relevant']:
            if not isinstance(value.get(k), bool):
                raise serializers.ValidationError(f'{k} must be boolean')
        return value


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ['id', 'name']


class SemesterLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SemesterLevel
        fields = ['id', 'name']


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


class CompanyEngagementScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyEngagementScope
        fields = [
            'id',
            'benefits_from_student',
            'has_value_or_research_project',
            'time_availability_and_participation',
            'workplace_has_conditions_for_group',
            'meeting_schedule_availability',
            'subject',
        ]


class CounterpartContactItemSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, allow_blank=True)
    counterpart_area = serializers.CharField(required=True, allow_blank=True)
    role = serializers.CharField(required=True, allow_blank=True)


class ProblemStatementSerializer(serializers.ModelSerializer):
    counterpart_contacts = CounterpartContactItemSerializer(many=True, required=False, default=default_counterpart_contacts)

    class Meta:
        model = ProblemStatement
        fields = [
            'id',
            'problem_to_address',
            'why_important',
            'stakeholders',
            'related_area',
            'benefits_short_medium_long_term',
            'problem_definition',
            'counterpart_contacts',
            'subject',
            'company',
        ]

