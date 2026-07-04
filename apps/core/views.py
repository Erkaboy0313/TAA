"""Core HTTP views (health check only for now)."""

from __future__ import annotations

from django.http import HttpRequest, JsonResponse


def health(_request: HttpRequest) -> JsonResponse:
    """Liveness probe consumed by the Dockerfile HEALTHCHECK."""
    return JsonResponse({"ok": True})
