from rest_framework import serializers
from .models import Company, ProblemStatement, CounterpartContact, CompanyEngagementScope
from rest_framework.validators import UniqueTogetherValidator
from subjects.models import Subject


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'address',
            'management_address',
            'email',
            'phone',
            'employees_count',
            'sector',
        ]


class CounterpartContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CounterpartContact
        fields = ['id', 'name', 'counterpart_area', 'role']


def _default_contacts_list():
    return [{"name": "", "counterpart_area": "", "role": ""}]


class ProblemStatementSerializer(serializers.ModelSerializer):
    counterpart_contacts = CounterpartContactSerializer(many=True, required=False)

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
        # No unique-together validation; allow multiple problem statements per subject-company

    def create(self, validated_data):
        contacts_data = validated_data.pop('counterpart_contacts', None)
        instance = ProblemStatement.objects.create(**validated_data)
        if not contacts_data:
            contacts_data = _default_contacts_list()
        for item in contacts_data:
            CounterpartContact.objects.create(problem_statement=instance, **item)
        return instance


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
            'company',
            'subject_code',
            'subject_section',
        ]
        validators = [
            UniqueTogetherValidator(
                queryset=CompanyEngagementScope.objects.all(),
                fields=['company', 'subject_code', 'subject_section'],
                message='Ya existe un alcance para esta empresa y asignatura'
            )
        ]

    def validate(self, attrs):
        subject_code = attrs.get('subject_code')
        subject_section = attrs.get('subject_section')

        # On update, fields might be omitted; fall back to instance values
        if self.instance is not None:
            if subject_code is None:
                subject_code = getattr(self.instance, 'subject_code', None)
            if subject_section is None:
                subject_section = getattr(self.instance, 'subject_section', None)

        # Ensure the referenced Subject exists
        if subject_code is None or subject_section is None:
            raise serializers.ValidationError({'subject_code': 'subject_code y subject_section son requeridos'})

        exists = Subject.objects.filter(code=subject_code, section=subject_section).exists()
        if not exists:
            raise serializers.ValidationError({'subject_code': 'No existe Subject con ese code y section'})

        return super().validate(attrs)

    def update(self, instance, validated_data):
        contacts_data = validated_data.pop('counterpart_contacts', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if contacts_data is not None:
            instance.counterpart_contacts.all().delete()
            for item in contacts_data:
                CounterpartContact.objects.create(problem_statement=instance, **item)
        return instance
