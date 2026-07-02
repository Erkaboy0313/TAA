"""Initial migration for the accounts app — creates the User table."""

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "telegram_id",
                    models.BigIntegerField(primary_key=True, serialize=False),
                ),
                ("username", models.CharField(blank=True, default="", max_length=64)),
                (
                    "language",
                    models.CharField(
                        choices=[
                            ("uz-Latn", "O'zbekcha (Latin)"),
                            ("uz-Cyrl", "Ўзбекча (Кирилл)"),
                            ("ru", "Русский"),
                        ],
                        default="uz-Latn",
                        max_length=8,
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "db_table": "accounts_user",
            },
        ),
    ]
