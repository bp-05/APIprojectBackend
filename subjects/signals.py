from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .events import publish_subject_event
from .models import Subject


def _publish(event_name, instance):
    try:
        publish_subject_event(event_name, instance)
    except Exception:
        # Avoid breaking save/delete operations if Redis is down
        pass


@receiver(post_save, sender=Subject)
def subject_saved(sender, instance, created, **kwargs):
    _publish("created" if created else "updated", instance)


@receiver(post_delete, sender=Subject)
def subject_deleted(sender, instance, **kwargs):
    _publish("deleted", instance)
