from rest_framework import serializers
from .models import Company


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'address',
            'management_address',
            'spys_responsible_name',
            'email',
            'phone',
            'employees_count',
            'sector',
            'api_type',
        ]

