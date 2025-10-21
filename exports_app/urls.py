from django.urls import path
from .views import export_forminstance

urlpatterns = [
    path('forms/<int:form_id>/export-xlsx/', export_forminstance, name='export_form_xlsx'),
]