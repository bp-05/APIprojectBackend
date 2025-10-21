import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_backend.settings')

# Create the celery app
app = Celery('api_backend')

# Load configuration from Django settings using namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all registered Django apps
app.autodiscover_tasks()