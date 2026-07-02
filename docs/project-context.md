---
project_name: 'TAA'
project_full_name: 'Tax Advisor Assistant'
user_name: 'Eric'
date: '2026-07-02'
version: '0.1'
status: 'active'
---

# Project Context — TAA (Tax Advisor Assistant)

> **Bu loyihada kod yozayotgan har bir AI agent (Claude Code, Copilot, subagents, future AI'lar) ushbu qoidalarni MAJBURIY o'qishi kerak. Bu — buzilmas qoidalar. Buzilmas degani, "bir vaqt uchun istisno" yo'q.** Sabab: Eric aynan shu qoidalarni **qoida sifatida** kiritdi — 2026-07-02.

---

## 0. Loyihaning bir gapda maqsadi

**O'zbek/rus tilida gaplashuvchi yangi tadbirkorlar uchun soliq, buxgalteriya va yuridik masalalar bo'yicha AI companion — Telegram bot + WebApp, voice-first, DavrOn/Azma/buxgalter.uz raqiblaridan farq qiladi.**

---

## 1. BUZILMAS QOIDALAR (The Golden Rules)

Har bir qoida — reddit rule, git hook, PR reviewer taqiqi. Buzilishi = revert.

### 🟢 R1 — Simplicity First (Oddiylik birinchi)

- **Eng oddiy yechim g'olib bo'ladi.** Agar 20 qatorli funksiya masalani hal qilsa, 200 qatorli "moslashuvchan" tuzilma yaratma.
- YAGNI (You Aren't Gonna Need It) — "kelajakda kerak bo'lishi mumkin" degan sabab bilan hech narsa qo'shilmaydi.
- Yangi abstraksiya = **kamida 3 marta takrorlanadigan** naqsh bo'lgandagina.
- Ikki oddiy funksiya har doim bitta "sehrli" funksiyadan yaxshi.

### 🟢 R2 — DRY (Don't Repeat Yourself), lekin aql bilan

- Bir xil kod 3+ joyda paydo bo'lsa → refactor.
- **Lekin**: xato DRY (turli mantiq'ni faqat shakl o'xshashligi uchun birlashtirish) — R1'ni buzadi. "Wrong abstraction is worse than duplication."
- Constants, config, string literal'lar — bir joyda (settings, enum, module-level).

### 🟢 R3 — SOLID (Django konteksti bilan)

- **S** — Single Responsibility. Bir view = bir maqsad. Bir service = bir domain amali. Bir model = bir entity.
- **O** — Open/Closed. Yangi feature = yangi service/handler qo'shish, mavjudni buzmaslik.
- **L** — Liskov. Subclass base'ning kontrakti'ni buzmaydi (kam ishlatiladi, lekin ishlatilsa — muhim).
- **I** — Interface Segregation. Katta service'lar o'rniga fokuslangan modullar.
- **D** — Dependency Inversion. Service'lar concrete client'ga emas, interface/callable'ga bog'liq (voice: Gemini client — interface, alternative provider qo'shilsa almashadi).

### 🟢 R4 — Clean Architecture (Layered, DDD-lite)

Har bir Django app quyidagi qatlamlarga bo'linadi:

```
<app>/
├── models.py          # DATA layer — schema + minimal invariants
├── services.py        # BUSINESS layer — write operations, orchestration
├── selectors.py       # BUSINESS layer — read queries, aggregations
├── views.py           # PRESENTATION layer — thin orchestration
├── handlers/          # (bot only) — Telegram bot handlers
├── serializers.py     # (agar API bo'lsa) — DTO / validation
├── exceptions.py      # Domain-specific exceptions
├── constants.py       # Enum, magic values
├── urls.py            # URL routing
├── admin.py           # Django admin (dev only)
├── migrations/
└── tests/
```

**Business logic view'da yoki model'da bo'lishi — ANTIPATTERN**. Darhol refactor.

### 🟢 R5 — Clean Code (Robert Martin)

- **Nomlar mazmunli**: `get_user_by_telegram_id` (yaxshi), `get_u` (yomon), `handle` (yomon), `process_data` (yomon).
- **Funksiyalar kichik**: 20 qatordan oshsa — bo'l. 5 argumentdan oshsa — dataclass/kwarg group.
- **Bir funksiya = bir abstraksiya darajasi.**
- **Type hints majburiy** har public funksiyada.
- **No magic numbers/strings** — har biri constant/enum.
- **No commented-out code** — git'ni ishlat.

### 🟢 R6 — NO Over-Engineering

Aniq belgilangan taqiqlar:

- ❌ **Repository pattern for Django ORM** — Django ORM allaqachon repository. Wrapper qo'shma.
- ❌ **Custom event bus** v1'da — direct function call yetadi.
- ❌ **Microservices** — monolith, bitta Django project.
- ❌ **GraphQL** — REST/HTMX yetadi.
- ❌ **Custom ORM** — Django ORM ishlat.
- ❌ **Dependency injection framework** (dependency-injector, wired) — Django allaqachon service layer beradi.
- ❌ **Abstract Base Classes "kelajakda kerak bo'lishi mumkin"** — konkret oling.
- ❌ **Design pattern namoyishlari** (Factory, Builder, Strategy) — agar Django + Python + oddiy funksiya yetsa — patternni tashla.
- ❌ **State machine library** (django-fsm) — oddiy `if/elif` yoki `TextChoices` bilan tugma qilinishi mumkin bo'lsa.
- ❌ **Retry/backoff library** — httpx allaqachon retry qo'llaydi, `tenacity` faqat murakkab holatda.
- ❌ **Test double / mock kutubxonalari zanjiri** — pytest'ning built-in `monkeypatch` yetadi.

**Qoida**: yangi kutubxona qo'shishdan oldin **stdlib + Django + hozirgi dependencies bilan qilib bo'lmasligi**ni isbotlash kerak.

### 🟢 R7 — Type Safety

- **Har public funksiya va class method — type hint bilan**:
  ```python
  def get_briefing(*, user: User, profile: EntrepreneurProfile) -> Briefing: ...
  ```
- **`Any` faqat runtime introspection'da** — boshqa joyda `mypy`/`pyright` warning'i qat'iy.
- **Optional aniq**: `str | None` (Python 3.10+ style), `Optional[str]` eski style — ishlatilmaydi.

### 🟢 R8 — Money & Data Integrity

- **`Decimal` only for money** — `float` **taqiqlangan**.
- **`Decimal` valyuta bilan** har doim (rekvizit va soliq summasi UZS/RUB/USD ajratilib saqlanadi).
- **UTC saqlash, mahalliy vaqt ko'rsatish** (`Asia/Tashkent` — display, `timezone.now()` — write).
- **Migration'lar prod'da zero-downtime**: NOT NULL constraint 3-step (add nullable → backfill → alter).

### 🟢 R9 — Voice & AI (Gemini) Rules

- **Audio in-memory only** — hech qachon diskka yozilmaydi, log'ga chiqmaydi.
- **Gemini timeout 30s** — undan oshsa graceful fail + retry option.
- **Gemini response untrusted** — har field validate qilinadi (`Decimal(payload['x'])` ValueError → user'ga tushunarli xato).
- **Confidence < 0.7 yoki ambiguous field bo'lsa** — user'ga clarification so'raladi, blind execute yo'q.
- **Voice endpoints async** (`async def`), ORM `sync_to_async` bilan.

### 🟢 R10 — Regulatory (ЗРУ-787, AI Law, PII)

- **Mahsulot pozitsiyasi**: "ma'lumot va ta'lim vositasi" (informational/educational), **pulli personalized tax consulting emas**.
- **Marketing / UI'da taqiqlangan iboralar**: "soliq maslahati beraman", "налоговое консультирование", "sizga X'ni tavsiya qilaman". O'rniga: "variantlar", "solishtirish", "hisoblash", "manba: lex.uz/..."
- **Har javob citation bilan** — lex.uz yoki soliq.uz URL yonida (RAG ground truth).
- **Har javob disclaimer** — footer'da: *"Bu ma'lumot vositasi. Muhim qarorlar uchun sertifikatli soliq maslahatchisiga murojaat qiling."*
- **AI content labeling** — bot javoblari "🤖 AI" prefix yoki footer bilan.
- **Human-in-the-loop escalation path** — user "sertifikatli maslahatchi kerak" desa yo'l ko'rsatiladi.
- **PII minimization** — INN, JSHSHIR saqlash faqat ROI bilan asoslangan bo'lsa. pd.gov.uz'ga baza ro'yxatga olinadi launch'dan oldin.
- **Log'da PII yo'q** — telegram_id hash bilan log'lanadi.

### 🟢 R11 — Testing (Pyramid)

- **Unit test'lar birinchi va ko'p** — services, selectors, pure functions.
- **Integration test'lar** — services + real Postgres (mock EMAS).
- **E2E** — bot handler flow (aiogram-test yoki manual).
- **Coverage baseline: ≥80% services/selectors**. Views — light.
- **Mock external only** — Gemini, lex.uz, Telegram API. **Never mock DB.**
- **Test isolation** — har test o'z fixture'iga ega, global state yo'q.
- **Naming**: `test_<what_happens>_when_<condition>`.

### 🟢 R12 — Git & Workflow (STRICT)

**Buzilmas git qoidalari** — Eric 2026-07-02 talabi:

- 🚫 **`main` branch'ga to'g'ridan-to'g'ri push TAQIQLANGAN.** Faqat PR orqali.
- ✅ **Har task = alohida branch = alohida PR.** Bitta branch'da bir necha task birlashtirish yo'q.
- ✅ **Branch nomi format**: `<type>/<epic-id>-<story-id>-<kalta-slug>`.
  - Misol: `feat/E03-S01-rag-embedding-service`, `fix/E05-S02-bot-webhook-timeout`, `chore/E00-S01-django-scaffold`.
  - `<type>` — `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`.
- ✅ **Commit messages — conventional, ingliz tilida**:
  ```
  feat(rag): add pgvector similarity search
  fix(bot): handle voice message without duration
  chore(deps): bump httpx to 0.28.1
  ```
- ✅ **Har commit — bitta mantiqiy o'zgarish**. God commits (100+ file, 5+ concern) — REVERT.
- ✅ **PR checklist** (har PR uchun majburiy):
  - [ ] Linked epic/story ID (masalan `Refs: E03-S01`)
  - [ ] AC bo'yicha ishlaydi (screenshot/video yoki test log)
  - [ ] Tests qo'shildi/yangilandi (Tester agent PR review)
  - [ ] `ruff check` + `ruff format --check` + `djlint --check` green
  - [ ] Migration reviewed (agar bo'lsa)
  - [ ] No `print()`, no `float`, no bare `except:`
  - [ ] Regulatoriy zonaga tegishli bo'lsa — R10 ban list check
  - [ ] `docs/*` yangilash kerakmi (arxitektura, PRD)?
- ✅ **PR merge shakli**: **squash merge** — `main` history tozaligini saqlaydi.
- ✅ **Har PR merge'dan so'ng**:
  - CI yashil (test + lint).
  - Docker image build muvaffaqiyatli.
  - **DevOps agent tekshiradi**: mahsulot deploy'ga tayyor holatda qoldimi?
  - Yashil bo'lmasa — revert va tuzat.
- ✅ **Pre-commit hooks** (`.pre-commit-config.yaml`) — buzilsa commit qabul qilinmaydi:
  - `ruff check --fix`
  - `ruff format`
  - `djlint --reformat`
  - `check-added-large-files` (>500KB block)
  - `detect-private-key`
- ✅ **Force push, `--no-verify`, `--amend after push` — TAQIQLANGAN** (main va shared branch'larda).
- ✅ **Feature branch qisqa umr ko'radi** — 5 kun ichida merge. Uzunroq bo'lsa: kichikroq PR'larga bo'l.

### 🟢 R13 — Continuous Deploy Readiness

- ✅ **Har story tugagach**: PR yopiladi → CI yashil → `main` branch **har vaqt** deploy'ga tayyor bo'lishi kerak.
- ✅ **Deploy avtomatik EMAS Faza 1'da** — lekin infrastruktura tayyor bo'ladi (Docker image, deploy script, Caddyfile, migration playbook).
- ✅ **Feature flag konvensiyasi**: yarim tayyor feature — env variable orqali off (`FEATURE_X_ENABLED=false`). Yarim tayyor kod hech qachon `main` da ishlamaydi.
- ✅ **DevOps agent har PR merge'dan so'ng auditsiya qiladi** — build succeeds, image tag'lanadi, oldingi image saqlanadi (rollback).



---

## 2. Texnik Stack (v1)

| Layer | Texnologiya | Versiya | Sabab |
|---|---|---|---|
| Runtime | Python | 3.12+ | async views + modern type hints |
| Framework | Django | 5.1 LTS | familiar (IWALLET), sync/async mix, batteries included |
| ASGI | uvicorn | latest | async views uchun |
| Database | PostgreSQL | 16+ | JSONB + pgvector (RAG uchun) |
| Vector store | **pgvector** extension | latest | **Alohida vector DB YO'Q** — Postgres ichida (R6) |
| Cache/Queue | Redis | 7.x | Celery broker + rate limit |
| Background | Celery + Beat | 5.4+ | lex.uz haftalik diff, deadline reminderlar |
| HTTP client | httpx | 0.28+ | async, retry built-in |
| LLM / STT / TTS | google-genai | 0.7+ | Gemini 2.0 flash — bitta provider unified |
| Bot | python-telegram-bot | 21.6+ | webhook mode |
| Frontend (Phase 2+) | htmx 2.0 + Alpine.js 3.14 + Tailwind 4 | — | IWALLET'dan qayta ishlatiladi |
| Settings | python-decouple | 3.8+ | `.env` — bitta `settings.py` (R6) |
| Tests | pytest + pytest-django + pytest-asyncio | latest | factory-boy fixtures |
| Lint/format | ruff | 0.7+ | bitta tool |
| Template lint | djlint | latest | pre-commit |
| Proxy/TLS | Caddy | 2.x | auto Let's Encrypt |
| Hosting | Single VPS + Managed Postgres | — | Hetzner / Neon |

**Dependency qo'shish qoidasi**: har yangi kutubxona commit message'da asoslanishi shart.

---

## 3. Django loyiha strukturasi

```
TAA/
├── docs/                        # PRD, architecture, project-context
├── .claude/agents/              # DevOps, Tester subagentlar
├── taa/                         # Django project (settings, urls, wsgi/asgi)
│   ├── settings.py              # SINGLE FILE — no base/dev/prod split (R6)
│   ├── urls.py
│   ├── asgi.py
│   └── celery.py
├── apps/
│   ├── core/                    # shared: TimestampedModel, base exceptions
│   ├── accounts/                # User, Telegram auth
│   ├── bot/                     # Telegram bot handlers, dispatchers
│   ├── rag/                     # RAG pipeline: embeddings, retrieval, prompt
│   ├── corpus/                  # Tax Code + BHMS ingestion, diff pipeline
│   ├── onboarding/              # "Yangi tadbirkor" wizard state machine
│   ├── briefing/                # Personalized briefing generation
│   ├── calculator/              # Regime simulator, tax calculators
│   ├── reminders/               # Deadline scheduler + push
│   ├── glossary/                # Plain-Uzbek term explanations
│   ├── documents/               # Template library
│   ├── checklist/               # Fine-prevention checklist
│   ├── itpark/                  # IT Park eligibility + guide
│   └── voice/                   # Gemini voice pipeline (STT+TTS)
├── requirements.txt
├── pyproject.toml               # ruff, pytest config
├── manage.py
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── Caddyfile
├── .pre-commit-config.yaml
├── .github/workflows/           # CI (test + lint)
├── CLAUDE.md                    # AI agent entry point
└── README.md
```

**App qo'shish qoidasi**: yangi domain (huquqiy ma'no bilan) paydo bo'lgandagina yangi app. Aksincha — mavjud app ichida module.

---

## 4. Code Style

### Ruff config (`pyproject.toml`)

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "UP", "DJ", "SIM", "RET", "ARG", "PL", "TCH", "TID"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["taa", "apps"]
combine-as-imports = true
```

### Nomlash

- `snake_case` — funksiya, o'zgaruvchi, modul, URL name
- `PascalCase` — class, dataclass, TypedDict
- `UPPER_SNAKE` — constant
- `kebab-case` — URL path, CSS class
- `_leading_underscore` — private

### Imports

```python
# stdlib
from decimal import Decimal
from datetime import datetime

# third-party
import httpx
from telegram import Update

# django
from django.db import models

# local
from apps.core.models import TimestampedModel
from apps.accounts.models import User
```

### Docstring

- Faqat **public services** va **complex selectors** — bitta qator, "what + when":
  ```python
  def generate_briefing(*, profile: EntrepreneurProfile) -> Briefing:
      """Build personalized tax briefing; raises CorpusMissingError if RAG index not ready."""
  ```
- **Args:/Returns:/Raises:** boilerplate — YO'Q, faqat noaniq holat bo'lsa.

### Comment

- **Faqat WHY non-obvious bo'lsa**:
  ```python
  # CBU.uz 0.00 qaytarsa — "mavjud emas", None sifatida
  if Decimal(payload['rate']) == 0: return None
  ```
- Har amal ustidagi izoh (`# increment counter`) — TAQIQLANGAN.

### File soft limits

- `.py` file — 300 qator (300+ bo'lsa split).
- Class — 200 qator.
- Function — 40 qator (40+ bo'lsa refactor).

---

## 5. Testing philosophy

### Piramida

```
      /\
     /E2E\        ~5% — 2-3 kritik flow (bot /start, RAG Q&A, briefing)
    /------\
   /  Integ \     ~25% — services + real Postgres
  /----------\
 /   Unit     \   ~70% — pure functions, selectors, calculators
/--------------\
```

### Fayl tuzilishi (co-located)

```
apps/onboarding/tests/
├── conftest.py       # pytest fixtures
├── factories.py      # factory-boy
├── test_models.py
├── test_services.py
├── test_selectors.py
├── test_handlers.py
└── test_integration.py
```

### Test qoidalari

- `pytest.mark.django_db` — DB kerak bo'lsa.
- `pytest.mark.asyncio` — async test.
- **Mock only external** — Gemini client, httpx to lex.uz, Telegram Bot API.
- **Real Postgres test DB** — mock emas.
- **Har test 1s dan tez** — sekin test = design smell.

---

## 6. DevOps philosophy

- **Local = Prod parity** — docker-compose har ikkalasida ishlaydi.
- **12-factor**: `.env`'dan config, no hardcode.
- **Deploy**: single VPS + Caddy + Docker + Postgres managed. Rollback — `current` symlink flip.
- **CI on GitHub Actions**: lint + test + build image. Auto-deploy main → prod.
- **Secrets**: never in git. `.env.example` — placeholder, `.env` — gitignored.
- **Monitoring v1**: logs (structured JSON) + basic uptime ping.
- **v2 monitoring**: Sentry (error) + Grafana (metrics).

---

## 7. Regulatoriy posture (R10 dan davomi)

### UI/UX language bank

**❌ Ishlatilmaydi**:
- "Sizga X rejimni tavsiya qilaman"
- "Bu — sizning optimal yechim"
- "Loophole", "soliqni kamaytirish taktikasi"
- "Soliq maslahati"
- Personal directive tilida ko'rsatma

**✅ Ishlatiladi**:
- "Sizning ma'lumotlaringizga ko'ra, quyidagi variantlar mavjud: A / B / C"
- "Har birining hisoblab chiqilgan yillik summasi:"
- "Manba: [Soliq Kodeksi 461-modda](https://lex.uz/...)"
- "Bu ma'lumot vositasi. Sertifikatli maslahatchi bilan tekshirilishi tavsiya etiladi."
- "Siz qaysi variantni tanlaysiz?"

### Har javob strukturasi

1. **Foydalanuvchi savoli** (voice yoki text).
2. **RAG chunk retrieval** — top 3-5 tegishli article.
3. **LLM synthesis** — citation'ni saqlab.
4. **UI**: matn + har fakt yonida `[manba]` link + footer disclaimer.

---

## 8. Erkin qoidalar (agar yuqoridagilar bilan ziddiyat bo'lmasa)

- Comment til: kod ichida — inglizcha; docstring — inglizcha; UX matn — o'zbek/rus.
- Var nomlari — inglizcha.
- Commit message — inglizcha.
- PRD / project docs — bilingual (o'zbek asosiy, inglizcha misol).

---

## 9. Antipattern qora ro'yxati (tez ma'lumotnoma)

| Antipattern | Buni qilma | O'rniga |
|---|---|---|
| Business logic view'da | ❌ | services.py |
| `float` money uchun | ❌ | Decimal |
| Bare `except:` | ❌ | `except SpecificError as e:` |
| `print()` prod'da | ❌ | logger.info/warning/error |
| Global state | ❌ | dependency inject |
| God class (500+ qator) | ❌ | split by responsibility |
| Repository wrapper Django ORM'da | ❌ | Manager + selectors |
| Custom event bus v1'da | ❌ | direct call |
| Commented-out code | ❌ | git delete |
| Magic number/string | ❌ | constants.py yoki Enum |
| Copy-paste 3+ marta | ❌ | function extraction |
| Test'da DB mock | ❌ | real test DB |
| Audio disk'ga yozish | ❌ | in-memory only |
| PII log | ❌ | hash yoki redact |
| Personalized "tavsiya qilaman" (regulated) | ❌ | "variantlar mavjud" |
| Har fikr uchun yangi kutubxona | ❌ | stdlib + Django birinchi |

---

## 10. Shubhalanganda

1. **Loyiha PRD'sini o'qi** (`docs/prd.md`)
2. **Architecture o'qi** (`docs/architecture.md`)
3. **Rules'ga qayt** (bu fayl)
4. **Simplicity darvozasidan o'tkiz** — 3 kishilik komandaga tushuntirsang kulishmaydigan yechim topguncha qayta ishla.
5. **Ericdan so'ra** — real ziddiyat bo'lsa.

---

**Har commit, har PR, har code review shu qoidalarga qarshi tekshiriladi. Buzilsa — revert. Istisno yo'q.**
