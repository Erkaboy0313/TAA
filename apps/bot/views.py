"""Bot HTTP views.

The webhook is the only public entry point. Telegram calls it whenever a
user sends a message; the secret embedded in the URL path (architecture
§9) is the authentication.
"""

from __future__ import annotations

import json
import logging

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.bot.dispatcher import dispatch_update

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
async def webhook(request: HttpRequest, secret: str) -> JsonResponse:
    """Receive a Telegram update, validate the URL secret, dispatch, ack.

    We answer 200 as fast as possible so Telegram does not retry — any
    heavy work (LLM, DB writes) is queued via Celery in later stories.
    """
    configured = settings.TELEGRAM_WEBHOOK_SECRET
    if not configured or secret != configured:
        # Do NOT reveal the reason — a fake 404 hides the endpoint entirely.
        raise Http404

    try:
        update = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.warning("bot.webhook.invalid_json")
        return HttpResponseBadRequest("invalid json")

    if not isinstance(update, dict) or "update_id" not in update:
        logger.warning("bot.webhook.invalid_update_shape")
        return HttpResponseBadRequest("invalid update shape")

    await dispatch_update(update)
    return JsonResponse({"ok": True})
