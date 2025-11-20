"""
Vistas para exportar datos a diferentes formatos.
"""
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from subjects.models import Subject
from .services import export_ficha_api, export_proyecto_api


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_ficha_api_view(request, subject_id: int):
    """
    Exporta la Ficha API de una asignatura en formato Excel.
    
    GET /api/exports/subjects/<subject_id>/ficha-api/
    
    Permisos:
    - El docente de la asignatura
    - Usuarios con rol 'admin' o 'VCM'
    
    NOTA: El sistema SIEMPRE genera un Excel válido, incluso si faltan datos.
    Los datos faltantes se llenan con cadenas vacías.
    """
    # Obtener la asignatura con todos los datos relacionados
    subject = get_object_or_404(
        Subject.objects.select_related(
            'area', 'career', 'semester', 'teacher'
        ).prefetch_related(
            'technical_competencies',
            'possible_counterparts__company',
            'possible_counterparts__interaction_types',
            'problem_statements__company',
            'problem_statements__counterpart_contacts',
            'units',
        ),
        id=subject_id
    )
    
    # Verificar permisos
    user = request.user
    is_teacher = subject.teacher and subject.teacher.id == user.id
    is_admin = user.is_staff or user.is_superuser
    is_vcm = getattr(user, 'role', None) in ['VCM', 'admin', 'coordinador']
    
    if not (is_teacher or is_admin or is_vcm):
        return Response(
            {'detail': 'No tienes permisos para exportar esta asignatura.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Generar y retornar el archivo Excel
    try:
        response = export_ficha_api(subject)
        
        # Agregar header informativo sobre datos faltantes (opcional)
        # El frontend puede leer esto para mostrar una advertencia
        # response['X-Export-Status'] = 'partial' si faltan datos, 'complete' si todo está
        
        return response
    except Exception as e:
        return Response(
            {'detail': f'Error al generar el archivo: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_proyecto_api_view(request, subject_id: int):
    """
    Exporta la Ficha Proyecto API de una asignatura en formato Excel.
    
    GET /api/exports/subjects/<subject_id>/proyecto-api/
    
    Permisos:
    - El docente de la asignatura
    - Usuarios con rol 'admin' o 'VCM'
    
    NOTA: El sistema SIEMPRE genera un Excel válido, incluso si faltan datos.
    Los datos faltantes se llenan con cadenas vacías.
    """
    # Obtener la asignatura con todos los datos relacionados
    subject = get_object_or_404(
        Subject.objects.select_related(
            'area', 'career', 'semester', 'teacher'
        ).prefetch_related(
            'problem_statements__counterpart_contacts',
            'units',
        ),
        id=subject_id
    )
    
    # Verificar permisos
    user = request.user
    is_teacher = subject.teacher and subject.teacher.id == user.id
    is_admin = user.is_staff or user.is_superuser
    is_vcm = getattr(user, 'role', None) in ['VCM', 'admin', 'coordinador']
    
    if not (is_teacher or is_admin or is_vcm):
        return Response(
            {'detail': 'No tienes permisos para exportar esta asignatura.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Generar y retornar el archivo Excel
    try:
        response = export_proyecto_api(subject)
        return response
    except Exception as e:
        return Response(
            {'detail': f'Error al generar el archivo: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
