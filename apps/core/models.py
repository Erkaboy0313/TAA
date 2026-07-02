"""Shared abstract models for TAA."""

from django.db import models


class TimestampedModel(models.Model):
    """Abstract base that stamps `created_at` and `updated_at` on every save.

    All concrete domain models should inherit from this instead of `models.Model`
    so audit trails are consistent across the codebase (project-context R4).
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
