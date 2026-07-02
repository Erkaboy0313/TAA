"""factory-boy factories for the accounts app."""

import factory
from factory.django import DjangoModelFactory

from apps.accounts.constants import Language
from apps.accounts.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    telegram_id = factory.Sequence(lambda n: 10_000_000 + n)
    username = factory.Faker("user_name")
    language = Language.UZ_LATIN
