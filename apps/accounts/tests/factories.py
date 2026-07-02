"""factory-boy factories for the accounts app."""

import factory
from factory.django import DjangoModelFactory

from apps.accounts.constants import Language
from apps.accounts.models import EntrepreneurProfile, User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    telegram_id = factory.Sequence(lambda n: 10_000_000 + n)
    username = factory.Faker("user_name")
    language = Language.UZ_LATIN


class ProfileFactory(DjangoModelFactory):
    class Meta:
        model = EntrepreneurProfile

    user = factory.SubFactory(UserFactory)
    profession_oked = ""
    expected_annual_revenue = None
    employee_count = 0
    has_foreign_clients = False
    is_it_sector = False
    current_status = ""
    chosen_regime = ""
    onboarding_step = ""
