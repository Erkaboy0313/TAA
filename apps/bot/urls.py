"""URL routes for the bot app."""

from django.urls import path

from apps.bot.views import webhook

app_name = "bot"

urlpatterns = [
    path("webhook/<str:secret>/", webhook, name="webhook"),
]
