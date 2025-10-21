from django.db import models

# Create your models here.
class Semester(models.Model):
    code = models.CharField(max_length=7, unique=True)  # ej: "2025-2"
    starts_at = models.DateField()
    ends_at = models.DateField()

    def __str__(self):
        return self.code