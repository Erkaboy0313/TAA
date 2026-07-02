"""Admin registrations for accounts. Gated by ADMIN_ENABLED (settings)."""

from django.conf import settings
from django.contrib import admin

from apps.accounts.models import EntrepreneurProfile, User

if settings.ADMIN_ENABLED:

    @admin.register(User)
    class UserAdmin(admin.ModelAdmin):
        list_display = ("telegram_id_hash", "username", "language", "created_at")
        # R10: never expose raw telegram_id as a search field — PII leak vector.
        search_fields = ("username",)
        readonly_fields = ("created_at", "updated_at", "telegram_id_hash")
        ordering = ("-created_at",)

    @admin.register(EntrepreneurProfile)
    class EntrepreneurProfileAdmin(admin.ModelAdmin):
        list_display = (
            "user",
            "employee_count",
            "has_foreign_clients",
            "is_it_sector",
            "current_status",
            "chosen_regime",
            "onboarding_step",
            "updated_at",
        )
        list_select_related = ("user",)
        search_fields = ()  # No PII search (R10). Regime/status filters are future work.
        readonly_fields = ("created_at", "updated_at")
        autocomplete_fields = ("user",)
