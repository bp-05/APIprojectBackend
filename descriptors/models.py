from django.db import models

# Create your models here.
class DescriptorFile(models.Model):
    subject  = models.ForeignKey('subjects.Subject', on_delete=models.CASCADE, related_name='descriptors')
    semester = models.ForeignKey('semesters.Semester', on_delete=models.PROTECT, related_name='descriptors')
    file = models.FileField(upload_to='descriptors/')
    is_scanned = models.BooleanField(default=False)
    text_cache = models.TextField(blank=True)
    meta = models.JSONField(default=dict, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('subject','semester')