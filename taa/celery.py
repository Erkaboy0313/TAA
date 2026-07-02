"""Celery application for TAA.

Minimum functional wiring (E00-S02): broker/backend read from Django
settings (`CELERY_*` namespace), tasks auto-discovered from installed apps.

Periodic schedules (lex.uz weekly sync, deadline daily push) land in
E02-S06 and E10-S04. `django-celery-beat`/`django-celery-results` are NOT
introduced here — that's a v2 optimisation (project-context R6).
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taa.settings")

app: Celery = Celery("taa")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
