from django.db import models

# Create your models here.
from django.conf import settings
from simple_history.models import HistoricalRecords

class FormTemplate(models.Model):
    key = models.SlugField(unique=True)  # "ficha-api" | "proyecto-api"
    version = models.CharField(max_length=10, default='v1')
    schema = models.JSONField()          # JSON Schema del formulario

    def __str__(self):
        return f"{self.key}@{self.version}"

class FormInstance(models.Model):
    subject  = models.ForeignKey('subjects.Subject', on_delete=models.CASCADE, related_name='forms')
    semester = models.ForeignKey('semesters.Semester', on_delete=models.PROTECT, related_name='forms')
    template = models.ForeignKey(FormTemplate, on_delete=models.PROTECT, related_name='instances')
    data     = models.JSONField(default=dict, blank=True)
    status   = models.CharField(max_length=20, default='draft')  # draft|in_review|approved
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    history = HistoricalRecords()

    class Meta:
        unique_together = ('subject', 'semester', 'template')