"""Attach TextChoices to the three profile enum fields (E01-S03)."""

from django.db import migrations, models

from apps.accounts.constants import CurrentStatus, OnboardingStep, Regime


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_entrepreneurprofile"),
    ]

    operations = [
        migrations.AlterField(
            model_name="entrepreneurprofile",
            name="chosen_regime",
            field=models.CharField(
                blank=True,
                choices=Regime.choices,
                default="",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="entrepreneurprofile",
            name="current_status",
            field=models.CharField(
                blank=True,
                choices=CurrentStatus.choices,
                default="",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="entrepreneurprofile",
            name="onboarding_step",
            field=models.CharField(
                choices=OnboardingStep.choices,
                default=OnboardingStep.NOT_STARTED,
                max_length=32,
            ),
        ),
    ]
