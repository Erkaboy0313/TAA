# TAA — Claude Code Session Entry

**Project**: TAA (Tax Advisor Assistant)
**Owner**: Eric
**Started**: 2026-07-02

> Har Claude Code session ushbu faylni birinchi o'qiydi. Bu — kirish nuqtasi. Detallar tegishli hujjatlarda.

---

## Loyihaning bir gapda

O'zbekiston yangi tadbirkorlari (YTT, MChJ, samozanyatos) uchun voice-first Telegram AI companion — soliq, buxgalteriya, yuridik masalalarda "5 yoshli bola" tilida yo'l ko'rsatadi, RAG + citation bilan.

---

## Majburiy o'qish (har session boshida)

1. **[docs/project-context.md](docs/project-context.md)** — BUZILMAS QOIDALAR (DRY, SOLID, Clean, no over-engineering, R1–R12).
2. **[docs/prd.md](docs/prd.md)** — mahsulot spec, 10 feature, 3 faza.
3. **[docs/architecture.md](docs/architecture.md)** — texnik qanday qurish.

**Ushbu 3 fayl ziddiyat bo'lsa** — project-context g'olib. Har PR shu qoidalarga qarshi tekshiriladi.

---

## Subagent ishlatish

- **DevOps ish** (Docker, CI, deploy, secrets, VPS): `.claude/agents/devops.md` — Winston.
- **Test ish** (test case, fixture, coverage, factory): `.claude/agents/tester.md` — Murat.
- **Umumiy kod yozish** (feature implementation): asosiy Claude o'zi qiladi, project-context'ga bo'ysunib.

---

## Session boshi checklist

- [ ] `docs/project-context.md` o'qidim (yoki cache'da bor).
- [ ] Vazifa aniq (feature, fix, deploy, test)?
- [ ] Qaysi Faza'ga tegishli (1, 2, 3)?
- [ ] Regulatoriy zonaga tegadimi (R10 ban list)?
- [ ] Yangi kutubxona qo'shishga to'g'ri kelmaydimi (R6)?

---

## Loyiha strukturasi (tez ma'lumot)

```
TAA/
├── docs/
│   ├── project-context.md    # BUZILMAS QOIDALAR
│   ├── product-brief.md
│   ├── prd.md                # 10 feature spec
│   └── architecture.md
├── .claude/agents/
│   ├── devops.md             # Winston (infra)
│   └── tester.md             # Murat (test)
├── taa/                      # Django project (settings, urls)
├── apps/                     # Django apps (per domain)
│   ├── core/                 # shared base
│   ├── accounts/             # User, Profile
│   ├── bot/                  # Telegram bot
│   ├── rag/                  # RAG pipeline
│   ├── corpus/               # lex.uz ingestion + diff
│   ├── onboarding/           # wizard state machine
│   ├── briefing/             # personalized briefing
│   ├── calculator/           # regime simulator
│   ├── reminders/            # deadline push
│   ├── glossary/             # plain-Uzbek terms
│   ├── documents/            # templates
│   ├── checklist/            # fine prevention
│   ├── itpark/               # IT Park eligibility
│   └── voice/                # Gemini STT/TTS
├── requirements.txt
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
├── Caddyfile
├── manage.py
└── .env.example
```

**Har app**: `models.py, services.py, selectors.py, exceptions.py, constants.py, tests/`.

---

## Golden reminders

1. **Simple wins** (R1).
2. **Decimal for money, no float** (R8).
3. **Business logic → services.py, not views/models** (R4).
4. **Test real Postgres, not mocked** (R11).
5. **No "tavsiya qilaman" personal directives in RAG output** (R10).
6. **Citation majburiy har RAG javobda** (R10).
7. **Audio in-memory only, no disk** (R9).
8. **Type hints majburiy** (R7).

---

## Xatolik holatida

- **Ziddiyat bor**: project-context R# ni ayt, ushlab tur, Ericdan so'ra.
- **YANGI abstraksiya keraк bo'lyapti**: birinchi "yo'q, 3 kopiya OK" darvozasidan o'tkaz. Uchinchi kopiya paydo bo'lsagina — refactor.
- **Test fail**: sabab yoz, tuzat, hech qachon xato bo'lgan test skip'lama.
- **Deploy'da xato**: rollback, sabab tekshir, keyin qayta.

---

## Foydali buyruqlar (Faza 1 boshlangandan so'ng)

```bash
# Dev
make dev              # docker-compose up
make migrate          # Django migrate
make shell            # Django shell

# Test
make test             # pytest full
make test-app APP=rag # pytest single app
make cov              # coverage report

# Lint
make lint             # ruff check + format --check
make fmt              # ruff format
```

*(DevOps agent Faza 1 boshida bu buyruqlarni tayyorlaydi.)*

---

Loyiha maqsadi: **buzilmas qoidalarga rioya qilib, oddiy, ishonchli, DUMB-proof mahsulot qurish**. Yaxshi kod = kelajakda tez keladigan. Yomon kod = kelajakda burnout keladigan.

**Har commit — refactor imkoni. Har PR — sifat qorovuli.**
