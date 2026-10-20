"""WSGI entrypoint. Deployment runs the production settings module."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "messycrm.settings.prod")

application = get_wsgi_application()
