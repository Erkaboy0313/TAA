"""Initial migration for the corpus app.

Creates the pgvector extension first (idempotent), then the `Document`
and `Chunk` tables with a 768-dim vector column and an HNSW index tuned
for cosine similarity search (m=16, ef_construction=64) —
architecture §4.
"""

import django.db.models.deletion
from django.db import migrations, models

from pgvector.django import HnswIndex, VectorExtension, VectorField


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        VectorExtension(),
        migrations.CreateModel(
            name="Document",
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
                ("source_url", models.URLField(unique=True)),
                ("title", models.CharField(max_length=255)),
                ("language", models.CharField(default="uz-Latn", max_length=8)),
            ],
            options={
                "verbose_name": "document",
                "verbose_name_plural": "documents",
                "db_table": "corpus_document",
            },
        ),
        migrations.CreateModel(
            name="Chunk",
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
                ("article_ref", models.CharField(blank=True, default="", max_length=32)),
                ("content", models.TextField()),
                ("embedding", VectorField(dimensions=768)),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chunks",
                        to="corpus.document",
                    ),
                ),
            ],
            options={
                "verbose_name": "chunk",
                "verbose_name_plural": "chunks",
                "db_table": "corpus_chunk",
                "indexes": [
                    HnswIndex(
                        name="chunk_embedding_idx",
                        fields=["embedding"],
                        m=16,
                        ef_construction=64,
                        opclasses=["vector_cosine_ops"],
                    ),
                ],
            },
        ),
    ]
