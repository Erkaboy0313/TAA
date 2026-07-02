# TAA — Tax Advisor Assistant

**Owner**: Eric
**Status**: 🟡 Planning → Implementation (Faza 1 kutmoqda)
**License**: TBD (private v1)

O'zbekiston yangi tadbirkorlari uchun voice-first Telegram AI companion — soliq, buxgalteriya, yuridik masalalarda "5 yoshli bola" tilida yo'l ko'rsatadi, RAG + citation bilan.

## Nima?

- **Telegram bot** (Faza 1) + **WebApp UI** (Faza 2) + **Public beta** (Faza 3).
- **Voice-first** — Uzbek/Russian voice message → tushunarli javob (matn + optional voice reply).
- **RAG + citation** — har javob lex.uz / soliq.uz manbasi bilan.
- **10 core feature** — Q&A, onboarding wizard, regime simulator, deadline reminder, tax code diff feed, fine checklist, hujjat shablonlari, IT Park guide, INN/MXIK lookup, plain-Uzbek glossariy.

## Kim uchun?

- Birinchi marta firma ochmoqchi (YTT, MChJ, samozanyatos).
- IT, ijodiy, xizmat, savdo sohalari.
- 25–40 yosh, o'zbek/rus tilida, Telegram'da faol.

## Documentation

- [Product Brief](docs/product-brief.md)
- [Product Requirements Document (PRD)](docs/prd.md)
- [Architecture](docs/architecture.md)
- [Project Context — UNBREAKABLE RULES](docs/project-context.md)

## AI Subagents

- [DevOps — Winston](.claude/agents/devops.md) — infrastruktura, deploy, CI.
- [Tester — Murat](.claude/agents/tester.md) — test yozish, coverage.

## Tech stack

Python 3.12+ · Django 5.1 · PostgreSQL 16 + pgvector · Redis 7 · Celery · python-telegram-bot 21+ · google-genai (Gemini 2.0) · httpx · htmx + Alpine.js + Tailwind 4 (Faza 2) · Docker + Caddy.

## Development

Copy `.env.example` to `.env` and fill values.

Common tasks (run from repo root):

```bash
make dev             # start stack (postgres, redis, app, celery)
make migrate         # apply DB migrations
make test            # run pytest inside the app container
make check           # lint + format --check + test (matches CI)
make down            # stop the stack
make help            # list all targets
```

URLs while `make dev` is running:
- Django app: <http://localhost:8000>
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

First-time contributors: `make precommit-install` once, so pre-commit hooks
run on every commit.

Admin (gated by `ADMIN_ENABLED`, defaults to `DEBUG`):

```bash
make dev
docker compose exec app python manage.py createsuperuser
# then visit http://localhost:8000/admin/
```

## Roadmap

- **Faza 1** (~10–14 hafta) — Bot MVP, barcha 10 feature.
- **Faza 2** (~6–8 hafta) — Telegram WebApp UI.
- **Faza 3** (~4–6 hafta) — Public beta + monetization.
- **Faza 4+** — Sertifikatli sherik integration (human review tier), IWALLET Suite cross-link.

## Contributing

Bu solo loyiha (v1). AI agentlar `docs/project-context.md` qoidalariga bo'ysunadi.

---

**Rules first. Simplicity always. Ship what matters.**
