from rest_framework import serializers
from .models import DescriptorFile

class DescriptorUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = DescriptorFile
        fields = ['id','subject','semester','file','is_scanned','text_cache','meta','processed_at']
        read_only_fields = ['text_cache','meta','processed_at']