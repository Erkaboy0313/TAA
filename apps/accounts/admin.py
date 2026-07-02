"""Admin registrations for accounts. Gated by ADMIN_ENABLED (settings)."""

from django.conf import settings
from django.contrib import admin

from apps.accounts.models import User

if settings.ADMIN_ENABLED:

    @admin.register(User)
    class UserAdmin(admin.ModelAdmin):
        list_display = ("telegram_id_hash", "username", "language", "created_at")
        # R10: never expose raw telegram_id as a search field — PII leak vector.
        search_fields = ("username",)
        readonly_fields = ("created_at", "updated_at", "telegram_id_hash")
        ordering = ("-created_at",)
