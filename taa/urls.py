"""Root URL configuration for TAA.

App-level routes land here in later stories (E05 bot webhook,
E09 briefing, etc.). Admin is env-gated via ADMIN_ENABLED (defaults
to DEBUG). Prod IP allowlist arrives with Faza 3 deploy plumbing.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path

admin.site.site_header = "TAA admin"
admin.site.site_title = "TAA admin"
admin.site.index_title = "TAA"

urlpatterns: list = []

if settings.ADMIN_ENABLED:
    urlpatterns += [path("admin/", admin.site.urls)]
