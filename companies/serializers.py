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
        fields = ['id', 'company', 'name', 'rut', 'phone', 'email', 'counterpart_area', 'role']
        extra_kwargs = {
            'company': {'required': False}
        }


def _default_contacts_list():
    return [{"name": "", "rut": "", "phone": "", "email": "", "counterpart_area": "", "role": ""}]


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
            CounterpartContact.objects.create(company=instance.company, **item)
        return instance

    def update(self, instance, validated_data):
        contacts_data = validated_data.pop('counterpart_contacts', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if contacts_data is not None:
            CounterpartContact.objects.filter(company=instance.company).delete()
            for item in contacts_data:
                CounterpartContact.objects.create(company=instance.company, **item)
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
            'subject_period_season',
            'subject_period_year',
        ]
        validators = [
            UniqueTogetherValidator(
                queryset=CompanyEngagementScope.objects.all(),
                fields=['company', 'subject_code', 'subject_section', 'subject_period_season', 'subject_period_year'],
                message='Ya existe un alcance para esta empresa y asignatura en ese periodo'
            )
        ]

    def validate(self, attrs):
        subject_code = attrs.get('subject_code')
        subject_section = attrs.get('subject_section')
        subject_period_season = attrs.get('subject_period_season')
        subject_period_year = attrs.get('subject_period_year')

        # On update, fields might be omitted; fall back to instance values
        if self.instance is not None:
            if subject_code is None:
                subject_code = getattr(self.instance, 'subject_code', None)
                attrs['subject_code'] = subject_code
            if subject_section is None:
                subject_section = getattr(self.instance, 'subject_section', None)
                attrs['subject_section'] = subject_section
            if subject_period_season is None:
                subject_period_season = getattr(self.instance, 'subject_period_season', None)
                attrs['subject_period_season'] = subject_period_season
            if subject_period_year is None:
                subject_period_year = getattr(self.instance, 'subject_period_year', None)
                attrs['subject_period_year'] = subject_period_year

        # Ensure the referenced Subject exists
        if None in (subject_code, subject_section, subject_period_season, subject_period_year):
            raise serializers.ValidationError(
                {'subject_code': 'subject_code, subject_section, subject_period_season y subject_period_year son requeridos'}
            )

        exists = Subject.objects.filter(
            code=subject_code,
            section=subject_section,
            period_season=subject_period_season,
            period_year=subject_period_year,
        ).exists()
        if not exists:
            raise serializers.ValidationError({'subject_code': 'No existe Subject con esa combinacion de code, section y periodo'})

        return super().validate(attrs)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
