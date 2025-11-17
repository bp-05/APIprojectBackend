from django.db.models.signals import post_save
from django.dispatch import receiver

from subjects.events import publish_subject_event

from .models import DescriptorFile


@receiver(post_save, sender=DescriptorFile)
def descriptor_processed(sender, instance, created, update_fields=None, **kwargs):
    """
    Emit a Subject SSE event when a descriptor finishes processing.
    """
    if not instance.subject_id:
        return
    if not instance.processed_at:
        return
    if update_fields is not None and "processed_at" not in update_fields:
        return
    try:
        publish_subject_event("descriptor_processed", instance.subject)
    except Exception:
        # SSE notifications should not interrupt the save pipeline
        pass
