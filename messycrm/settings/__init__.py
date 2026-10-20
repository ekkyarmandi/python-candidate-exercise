"""Environment-specific Django settings.

Nothing imports this package directly: the active module is chosen with
``DJANGO_SETTINGS_MODULE``.

===============================  ===========================================
``messycrm.settings.local``      Development. ``manage.py`` defaults to this.
``messycrm.settings.test``       Test suite and CI. Hermetic, no secrets.
``messycrm.settings.prod``       Deployment. ``wsgi.py`` defaults to this.
===============================  ===========================================
"""
