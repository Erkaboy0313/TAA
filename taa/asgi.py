"""ASGI entry point for TAA (used by uvicorn for async views)."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taa.settings")

application = get_asgi_application()
