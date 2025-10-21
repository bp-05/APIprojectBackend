from rest_framework import serializers
from .models import Subject

class SubjectSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'code', 'name', 'api_flag', 'teacher', 'teacher_name']