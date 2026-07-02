"""Root URL configuration for TAA.

App-level routes land here in later stories (E05 bot webhook,
E09 briefing, etc.). Admin gated by DEBUG until E00-S09.
"""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
