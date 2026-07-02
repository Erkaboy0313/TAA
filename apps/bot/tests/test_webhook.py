"""Tests for the /bot/webhook/<secret>/ endpoint (E05-S02)."""

from __future__ import annotations

import json
import logging
from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest

from django.http import Http404
from django.test import AsyncClient, AsyncRequestFactory
from django.test.utils import override_settings

from apps.bot.views import webhook as webhook_view

VALID_UPDATE: dict = {
    "update_id": 1,
    "message": {
        "message_id": 42,
        "date": 1700000000,
        "chat": {"id": 123, "type": "private"},
        "from": {"id": 123, "is_bot": False, "first_name": "Aziza"},
        "text": "Salom",
    },
}

DISTINCT_UPDATE_ID = 9876


@pytest.fixture(autouse=True)
def _disable_ssl_redirect(settings):  # noqa: PT004
    # DEBUG=False (as in CI) enables SECURE_SSL_REDIRECT and every plain HTTP
    # request from AsyncClient gets a 301 before it ever hits our view. The
    # X-Forwarded-Proto trick does not propagate through the async pipeline
    # cleanly, so we disable the redirect for the whole webhook test module.
    # The redirect itself is exercised by Django's own security tests; our
    # concern here is the view contract.
    settings.SECURE_SSL_REDIRECT = False


@pytest.fixture
def client() -> AsyncClient:
    return AsyncClient()


@pytest.fixture
def dispatch_mock(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    mock = AsyncMock(return_value=None)
    monkeypatch.setattr("apps.bot.views.dispatch_update", mock)
    return mock


@override_settings(TELEGRAM_WEBHOOK_SECRET="test-secret")
@pytest.mark.asyncio
async def test_webhook_returns_200_when_secret_and_body_valid(
    client: AsyncClient, dispatch_mock: AsyncMock
) -> None:
    resp = await client.post(
        "/bot/webhook/test-secret/",
        data=json.dumps(VALID_UPDATE),
        content_type="application/json",
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {"ok": True}
    assert resp["Content-Type"].startswith("application/json")
    dispatch_mock.assert_awaited_once()
    assert dispatch_mock.await_args.args[0]["update_id"] == 1


# The 404 cases call the view directly via AsyncRequestFactory rather than
# AsyncClient. The full client stack turns Http404 into a rendered 404
# template, which is (a) not what we care about (the view's contract is
# "raise Http404") and (b) currently trips a Django 5.1 + Python 3.14
# `Context.__copy__` incompat during template rendering. Asserting the
# raised exception directly is both a tighter contract check and portable.
@override_settings(TELEGRAM_WEBHOOK_SECRET="test-secret")
@pytest.mark.asyncio
async def test_webhook_raises_404_when_secret_wrong(dispatch_mock: AsyncMock) -> None:
    factory = AsyncRequestFactory()
    request = factory.post(
        "/bot/webhook/not-the-secret/",
        data=json.dumps(VALID_UPDATE),
        content_type="application/json",
    )
    with pytest.raises(Http404):
        await webhook_view(request, secret="not-the-secret")
    dispatch_mock.assert_not_awaited()


@override_settings(TELEGRAM_WEBHOOK_SECRET="")
@pytest.mark.asyncio
async def test_webhook_raises_404_when_configured_secret_is_empty(
    dispatch_mock: AsyncMock,
) -> None:
    # Production misconfig: unset secret must NOT accept any URL — otherwise
    # attacker could POST to /bot/webhook//.
    factory = AsyncRequestFactory()
    request = factory.post(
        "/bot/webhook/anything/",
        data=json.dumps(VALID_UPDATE),
        content_type="application/json",
    )
    with pytest.raises(Http404):
        await webhook_view(request, secret="anything")
    dispatch_mock.assert_not_awaited()


@override_settings(TELEGRAM_WEBHOOK_SECRET="test-secret")
@pytest.mark.asyncio
async def test_webhook_returns_405_when_method_is_get(
    client: AsyncClient, dispatch_mock: AsyncMock
) -> None:
    resp = await client.get("/bot/webhook/test-secret/")
    assert resp.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    dispatch_mock.assert_not_awaited()


@override_settings(TELEGRAM_WEBHOOK_SECRET="test-secret")
@pytest.mark.asyncio
async def test_webhook_returns_400_when_body_is_invalid_json(
    client: AsyncClient, dispatch_mock: AsyncMock
) -> None:
    resp = await client.post(
        "/bot/webhook/test-secret/",
        data="not json at all {",
        content_type="application/json",
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    dispatch_mock.assert_not_awaited()


@override_settings(TELEGRAM_WEBHOOK_SECRET="test-secret")
@pytest.mark.asyncio
@pytest.mark.parametrize("payload", ["[]", '"hi"', "null", "42"])
async def test_webhook_returns_400_when_body_is_not_an_object(
    client: AsyncClient, dispatch_mock: AsyncMock, payload: str
) -> None:
    resp = await client.post(
        "/bot/webhook/test-secret/",
        data=payload,
        content_type="application/json",
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    dispatch_mock.assert_not_awaited()


@override_settings(TELEGRAM_WEBHOOK_SECRET="test-secret")
@pytest.mark.asyncio
async def test_webhook_returns_400_when_update_id_missing(
    client: AsyncClient, dispatch_mock: AsyncMock
) -> None:
    resp = await client.post(
        "/bot/webhook/test-secret/",
        data=json.dumps({"message": {"text": "hi"}}),
        content_type="application/json",
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    dispatch_mock.assert_not_awaited()


@override_settings(TELEGRAM_WEBHOOK_SECRET="test-secret")
@pytest.mark.asyncio
async def test_webhook_dispatches_the_exact_parsed_update_dict(
    client: AsyncClient, dispatch_mock: AsyncMock
) -> None:
    update = {
        "update_id": DISTINCT_UPDATE_ID,
        "message": {"text": "keeps its shape"},
    }
    resp = await client.post(
        "/bot/webhook/test-secret/",
        data=json.dumps(update),
        content_type="application/json",
    )
    assert resp.status_code == HTTPStatus.OK
    dispatch_mock.assert_awaited_once()
    (arg,) = dispatch_mock.await_args.args
    assert arg == update
    assert arg["update_id"] == DISTINCT_UPDATE_ID


@override_settings(TELEGRAM_WEBHOOK_SECRET="test-secret")
@pytest.mark.asyncio
async def test_webhook_logs_do_not_contain_raw_message_text(
    client: AsyncClient,
    dispatch_mock: AsyncMock,  # noqa: ARG001  (patch is applied by the fixture)
    caplog: pytest.LogCaptureFixture,
) -> None:
    # R10: PII / user content must never appear in logs. Feed a distinctive
    # string and assert it is absent from every captured record.
    distinctive = "SECRET-INN-123456789-DO-NOT-LOG"
    update = {
        "update_id": 7,
        "message": {
            "message_id": 1,
            "date": 1700000000,
            "chat": {"id": 1, "type": "private"},
            "from": {"id": 1, "is_bot": False, "first_name": "X"},
            "text": distinctive,
        },
    }
    with caplog.at_level(logging.DEBUG, logger="apps.bot"):
        resp = await client.post(
            "/bot/webhook/test-secret/",
            data=json.dumps(update),
            content_type="application/json",
        )
    assert resp.status_code == HTTPStatus.OK
    for record in caplog.records:
        assert distinctive not in record.getMessage()
        assert distinctive not in str(getattr(record, "args", "") or "")
