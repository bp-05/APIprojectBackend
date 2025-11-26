from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .events import publish_subject_event
from .models import Subject, SubjectPhaseProgress


def _publish(event_name, instance):
    try:
        publish_subject_event(event_name, instance)
    except Exception:
        # Avoid breaking save/delete operations if Redis is down
        pass


@receiver(post_save, sender=Subject)
def subject_saved(sender, instance, created, **kwargs):
    _publish("created" if created else "updated", instance)
    
    # Al crear una asignatura, crear los 3 registros de progreso de fases con estado "nr"
    if created:
        create_default_phase_progress(instance)


@receiver(post_delete, sender=Subject)
def subject_deleted(sender, instance, **kwargs):
    _publish("deleted", instance)


def create_default_phase_progress(subject):
    """Crea los registros de progreso de fases por defecto para una asignatura.
    
    Crea 3 registros (formulacion, gestion, validacion) con estado 'nr' (no realizado).
    Si ya existen registros para alguna fase, no los sobrescribe.
    """
    phases = ['formulacion', 'gestion', 'validacion']
    for phase in phases:
        SubjectPhaseProgress.objects.get_or_create(
            subject=subject,
            phase=phase,
            defaults={'status': 'nr'}
        )
