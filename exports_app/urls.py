"""
URLs para la app de exportaciones.
"""
from django.urls import path
from .views import export_ficha_api_view, export_proyecto_api_view

app_name = 'exports'

urlpatterns = [
    path('exports/subjects/<int:subject_id>/ficha-api/', export_ficha_api_view, name='export_ficha_api'),
    path('exports/subjects/<int:subject_id>/proyecto-api/', export_proyecto_api_view, name='export_proyecto_api'),
]