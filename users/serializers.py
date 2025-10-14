from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserMeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id','username','email','first_name','last_name','full_name','role','is_staff','is_superuser','date_joined']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','email','first_name','last_name','role','is_active']