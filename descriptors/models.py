from django.db import models

# Create your models here.
class DescriptorFile(models.Model):
    subject  = models.ForeignKey('subjects.Subject', on_delete=models.CASCADE, related_name='descriptors', null=True, blank=True)
    file = models.FileField(upload_to='descriptors/')
    is_scanned = models.BooleanField(default=False)
    text_cache = models.TextField(blank=True)
    # Texto destilado para visualización en admin (colapso de espacios y recorte)
    text_distilled = models.TextField(blank=True)
    meta = models.JSONField(default=dict, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['subject'], name='unique_descriptor_per_subject')
        ]
