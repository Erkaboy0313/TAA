"""TAA project package.

Re-export the Celery app so `celery -A taa` picks it up and Django boots
it early (needed for shared_task decorators to register).
"""
from taa.celery import app as celery_app

__all__: tuple[str, ...] = ("celery_app",)
