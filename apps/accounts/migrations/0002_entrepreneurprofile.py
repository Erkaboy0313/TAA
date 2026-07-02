"""Add EntrepreneurProfile — the tadbirkor profile the wizard fills."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EntrepreneurProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profession_oked",
                    models.CharField(blank=True, default="", max_length=10),
                ),
                (
                    "expected_annual_revenue",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=15,
                        null=True,
                    ),
                ),
                ("employee_count", models.PositiveIntegerField(default=0)),
                ("has_foreign_clients", models.BooleanField(default=False)),
                ("is_it_sector", models.BooleanField(default=False)),
                (
                    "current_status",
                    models.CharField(blank=True, default="", max_length=32),
                ),
                (
                    "chosen_regime",
                    models.CharField(blank=True, default="", max_length=32),
                ),
                (
                    "onboarding_step",
                    models.CharField(blank=True, default="", max_length=32),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to="accounts.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "entrepreneur profile",
                "verbose_name_plural": "entrepreneur profiles",
                "db_table": "accounts_profile",
            },
        ),
    ]
