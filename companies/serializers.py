from rest_framework import serializers
from .models import Company, ProblemStatement, CounterpartContact
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
        if contacts_data:
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



