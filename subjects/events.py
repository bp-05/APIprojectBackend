import json
from contextlib import contextmanager

import redis
from django.conf import settings


SUBJECT_EVENTS_CHANNEL = "subjects:events"


def _get_redis_client():
    url = getattr(settings, "SUBJECT_STREAM_REDIS_URL", None) or settings.CELERY_BROKER_URL
    return redis.Redis.from_url(url, decode_responses=True)


def publish_subject_event(event_type, subject):
    """
    Publish a small payload describing the change to a Subject instance.
    """
    updated_at = getattr(subject, "updated_at", None)
    payload = {
        "event": event_type,
        "subject_id": subject.id,
        "code": subject.code,
        "section": subject.section,
        "name": subject.name,
        "period_year": subject.period_year,
        "period_season": subject.period_season,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }
    _get_redis_client().publish(SUBJECT_EVENTS_CHANNEL, json.dumps(payload))


@contextmanager
def subject_event_stream():
    """
    Subscribe to subject events and yield a Redis pub/sub iterator.
    """
    client = _get_redis_client()
    pubsub = client.pubsub()
    pubsub.subscribe(SUBJECT_EVENTS_CHANNEL)
    try:
        yield pubsub.listen()
    finally:
        pubsub.close()
