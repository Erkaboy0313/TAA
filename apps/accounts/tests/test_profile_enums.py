"""Tests for the profile enum contracts introduced in E01-S03.

Covers three things:
1. Enum membership contracts — each set's DB values are the documented ones.
2. Model defaults — a fresh profile lands in `OnboardingStep.NOT_STARTED`.
3. Round-trip persistence + `full_clean()` validation of `choices=`.
"""

import pytest

from django.core.exceptions import ValidationError

from apps.accounts.constants import CurrentStatus, OnboardingStep, Regime

REGIME_DB_VALUES = {
    "samozanyatos",
    "ytt_4",
    "ytt_25m",
    "mchj_simplified",
    "mchj_general",
    "mchj_it_park",
}

CURRENT_STATUS_DB_VALUES = {
    "not_started",
    "planning",
    "active_lt_6mo",
    "active_ge_6mo",
}

ONBOARDING_STEP_DB_VALUES = {
    "not_started",
    "ask_profession",
    "ask_revenue",
    "ask_employees",
    "ask_foreign_clients",
    "ask_it_sector",
    "ask_current_status",
    "generate_briefing",
    "complete",
}


@pytest.mark.parametrize("value", sorted(REGIME_DB_VALUES))
def test_regime_contains_expected_db_value(value):
    assert value in Regime.values


def test_regime_has_exactly_six_documented_values():
    assert set(Regime.values) == REGIME_DB_VALUES


@pytest.mark.parametrize("value", sorted(CURRENT_STATUS_DB_VALUES))
def test_current_status_contains_expected_db_value(value):
    assert value in CurrentStatus.values


def test_current_status_has_exactly_four_documented_values():
    assert set(CurrentStatus.values) == CURRENT_STATUS_DB_VALUES


@pytest.mark.parametrize("value", sorted(ONBOARDING_STEP_DB_VALUES))
def test_onboarding_step_contains_expected_db_value(value):
    assert value in OnboardingStep.values


def test_onboarding_step_has_exactly_nine_documented_values():
    assert set(OnboardingStep.values) == ONBOARDING_STEP_DB_VALUES


@pytest.mark.parametrize(
    "enum_cls,expected_size",
    [
        (Regime, 6),
        (CurrentStatus, 4),
        (OnboardingStep, 9),
    ],
)
def test_choices_return_unique_db_value_label_pairs(enum_cls, expected_size):
    choices = enum_cls.choices
    assert isinstance(choices, list)
    assert len(choices) == expected_size
    db_values = [db_value for db_value, _label in choices]
    assert len(set(db_values)) == expected_size
    for db_value, label in choices:
        assert isinstance(db_value, str)
        assert db_value != ""
        # `label` is a lazy proxy; forcing str resolves gettext_lazy.
        assert str(label) != ""


@pytest.mark.django_db
def test_profile_defaults_onboarding_step_to_not_started_when_created(profile_factory):
    profile = profile_factory()
    assert profile.onboarding_step == OnboardingStep.NOT_STARTED
    profile.refresh_from_db()
    assert profile.onboarding_step == OnboardingStep.NOT_STARTED


@pytest.mark.django_db
def test_chosen_regime_round_trips_when_set_to_valid_enum(profile_factory):
    profile = profile_factory(chosen_regime=Regime.YTT_4)
    profile.refresh_from_db()
    assert profile.chosen_regime == Regime.YTT_4
    assert profile.chosen_regime == "ytt_4"


@pytest.mark.django_db
def test_current_status_round_trips_when_set_to_valid_enum(profile_factory):
    profile = profile_factory(current_status=CurrentStatus.ACTIVE_LT_6MO)
    profile.refresh_from_db()
    assert profile.current_status == CurrentStatus.ACTIVE_LT_6MO
    assert profile.current_status == "active_lt_6mo"


@pytest.mark.django_db
def test_onboarding_step_round_trips_when_set_to_valid_enum(profile_factory):
    profile = profile_factory(onboarding_step=OnboardingStep.ASK_REVENUE)
    profile.refresh_from_db()
    assert profile.onboarding_step == OnboardingStep.ASK_REVENUE
    assert profile.onboarding_step == "ask_revenue"


@pytest.mark.django_db
def test_full_clean_rejects_off_enum_chosen_regime_but_save_still_persists(profile_factory):
    # Django `choices=` is enforced by `full_clean()`, not by the DB writer —
    # the row still saves, but validation must flag the value.
    profile = profile_factory(chosen_regime="not_a_real_regime")
    profile.refresh_from_db()
    assert profile.chosen_regime == "not_a_real_regime"
    with pytest.raises(ValidationError) as exc_info:
        profile.full_clean()
    assert "chosen_regime" in exc_info.value.error_dict
