from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from forms_app.models import FormInstance
from .services import export_form_to_xlsx, get_template_path

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_forminstance(request, form_id: int):
    form = get_object_or_404(FormInstance.objects.select_related('subject','template'), id=form_id)
    user = request.user
    if not (user.is_staff or getattr(user, 'role', None) == 'VCM' or user.groups.filter(name__in=['vcm']).exists() or form.subject.teacher_id == user.id):
        return Response({'detail': 'No autorizado.'}, status=status.HTTP_403_FORBIDDEN)
    template_path = get_template_path(form.template.key)
    return export_form_to_xlsx(form, template_path)
