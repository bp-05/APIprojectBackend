
# Create your models here.
from django.db import models
from django.conf import settings

class Subject(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    api_flag = models.BooleanField(default=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='subjects')

    def __str__(self):
        return f"{self.code} - {self.name}"