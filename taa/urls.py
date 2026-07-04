"""Root URL configuration for TAA.

Bot webhook mounted at /bot/. Admin is env-gated via ADMIN_ENABLED
(defaults to DEBUG). Prod IP allowlist arrives with Faza 3 deploy plumbing.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from apps.core.views import health

admin.site.site_header = "TAA admin"
admin.site.site_title = "TAA admin"
admin.site.index_title = "TAA"

urlpatterns: list = [
    path("health/", health, name="health"),
    path("bot/", include("apps.bot.urls")),
]

if settings.ADMIN_ENABLED:
    urlpatterns += [path("admin/", admin.site.urls)]
