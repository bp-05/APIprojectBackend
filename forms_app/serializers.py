from rest_framework import serializers
from jsonschema import validate, ValidationError
from .models import FormTemplate, FormInstance

class FormTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormTemplate
        fields = ['id', 'key', 'version', 'schema']

class FormInstanceSerializer(serializers.ModelSerializer):
    template_key = serializers.CharField(source='template.key', read_only=True)
    class Meta:
        model = FormInstance
        fields = ['id','subject','semester','template','template_key','data','status','updated_by']
        read_only_fields = ['updated_by']

    def validate(self, attrs):
        data = attrs.get('data', getattr(self.instance, 'data', {}))
        template = attrs.get('template', getattr(self.instance, 'template', None))
        if template and template.schema:
            try:
                validate(instance=data, schema=template.schema)
            except ValidationError as e:
                raise serializers.ValidationError({'data': f'JSON no cumple schema: {e.message}'})
        return attrs

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)