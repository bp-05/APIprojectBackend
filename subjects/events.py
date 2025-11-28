import asyncio
import json
from contextlib import contextmanager

import redis
import redis.asyncio as aioredis
from django.conf import settings


SUBJECT_EVENTS_CHANNEL = "subjects:events"


def _get_redis_client():
    url = getattr(settings, "SUBJECT_STREAM_REDIS_URL", None) or settings.CELERY_BROKER_URL
    return redis.Redis.from_url(url, decode_responses=True)


def _get_redis_url():
    return getattr(settings, "SUBJECT_STREAM_REDIS_URL", None) or settings.CELERY_BROKER_URL


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
    (Synchronous version - kept for backwards compatibility)
    """
    client = _get_redis_client()
    pubsub = client.pubsub()
    pubsub.subscribe(SUBJECT_EVENTS_CHANNEL)
    try:
        yield pubsub.listen()
    finally:
        pubsub.close()


async def async_subject_event_stream():
    """
    Async generator that subscribes to subject events via Redis pub/sub.
    Compatible with ASGI servers like Uvicorn.
    """
    url = _get_redis_url()
    client = aioredis.from_url(url, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe(SUBJECT_EVENTS_CHANNEL)
    try:
        while True:
            try:
                message = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True), timeout=30.0)
                if message is not None:
                    yield message
                else:
                    # Send keepalive comment every 30s to keep connection alive
                    yield {"type": "keepalive"}
            except asyncio.TimeoutError:
                # Send keepalive comment to keep connection alive
                yield {"type": "keepalive"}
            except asyncio.CancelledError:
                break
    finally:
        await pubsub.close()
        await client.close()
