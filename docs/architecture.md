# TAA — Architecture

**Version:** 0.1
**Date:** 2026-07-02
**Author:** John (PM) + Winston (Architect)
**Status:** Draft

> Bu hujjat mahsulotning **qanday** qurilishini yozadi. **Nima** — `docs/prd.md`. Kod qoidalari — `docs/project-context.md`. Buzilmas qoidalarga zid arxitektura qarori — mavjud emas.

---

## 1. Arxitektura falsafasi

1. **Bot-first, WebApp-later** — Faza 1 monolithic Django + python-telegram-bot. WebApp qatlami Faza 2'da mavjud arxitektura ustida qo'shiladi (view'lar + template'lar).
2. **Monolith + apps** — mikroservis YO'Q. Bitta Django project, domain'lar apps'da (project-context §3).
3. **Single settings.py** — env-driven, no base/dev/prod split.
4. **Sync + Async selective** — voice/RAG endpoints async, boshqasi sync. `sync_to_async` bilan ORM async view'da.
5. **Managed complexity boundaries** — RAG pipeline, Voice pipeline, Corpus pipeline — har biri o'z app'ida, contract'lari services.py orqali.
6. **Provider abstraction** — Gemini client interface (`apps/voice/providers/`), kelajakda OpenAI/Vertex almashish oson.
7. **Postgres birinchi va oxirgisi** — vector, cache (kichik), relational hammasi bir joyda. Redis faqat Celery uchun.

---

## 2. Yuqori-daraja diagram

```
                              ┌─────────────────┐
                              │  Telegram User  │
                              └────────┬────────┘
                                       │  (text / voice message)
                                       ▼
                              ┌─────────────────┐
                              │  Telegram API   │
                              └────────┬────────┘
                                       │  webhook (HTTPS)
                                       ▼
     ┌────────────────────────────────────────────────────────────┐
     │                    Caddy (TLS, reverse proxy)              │
     └────────────────┬───────────────────────────┬───────────────┘
                      │                           │
                      ▼                           ▼
              ┌─────────────┐              ┌─────────────┐
              │  ASGI (uv)  │              │  WebApp UI  │
              │  Django     │              │  (Phase 2+) │
              └──────┬──────┘              └──────┬──────┘
                     │                            │
        ┌────────────┼────────────┬───────────────┘
        │            │            │
        ▼            ▼            ▼
   ┌────────┐  ┌─────────┐  ┌──────────┐
   │  bot   │  │  rag    │  │  voice   │
   │ app    │  │  app    │  │  app     │
   └───┬────┘  └────┬────┘  └────┬─────┘
       │            │            │
       │       ┌────┴────┐       │
       │       │         │       │
       │       ▼         ▼       │
       │   ┌──────┐  ┌──────┐   │
       │   │corpus│  │gemini│   │
       │   │ app  │  │client│◄──┘
       │   └──┬───┘  └──────┘
       │      │
       ▼      ▼
   ┌────────────────────────────────┐
   │  PostgreSQL 16 + pgvector      │
   │  ─ Users, Profiles, Briefings  │
   │  ─ Corpus chunks + embeddings  │
   │  ─ Reminders, Diffs, Docs      │
   └────────────────────────────────┘

                  ┌──────────────────┐
                  │  Celery + Redis  │
                  │  ─ Weekly lex.uz  │
                  │    diff scrape   │
                  │  ─ Deadline push │
                  │  ─ Reminders     │
                  └──────────────────┘

     External:
     ┌───────────┐  ┌────────┐  ┌───────────┐
     │  Gemini   │  │ lex.uz │  │ soliq API │
     └───────────┘  └────────┘  └───────────┘
```

---

## 3. Django apps (project-context §3'ga muvofiq)

Har app: `models.py, services.py, selectors.py, exceptions.py, constants.py, tests/`.

### `apps/core/`
- `TimestampedModel` (created_at, updated_at abstract)
- Shared exceptions (`DomainError`)
- Utility function'lar (currency formatter, date formatter Asia/Tashkent)
- **Yo'q**: business logic, model, service.

### `apps/accounts/`
- **Models**: `User(telegram_id PK, username, language, locale, created_at)`, `EntrepreneurProfile(user_fk, profession_oked, expected_annual_revenue, employee_count, has_foreign_clients, is_it_sector, current_status, chosen_regime)`.
- **Services**: `create_user_from_telegram`, `update_profile`.
- **Selectors**: `get_by_telegram_id`, `get_profile`.
- **Middleware**: `TelegramWebAppAuthMiddleware` — Faza 2'da (bot webhook alohida).

### `apps/bot/`
- **Handlers**: `/start`, `/help`, `/ask`, `/briefing`, `/simulyator`, `/checklist`, `/documents`, `/it_park`, `/inn`, `/mxik`, `/reminders_on/off`, `/glossary`, `/voice_on/off`.
- **Router**: python-telegram-bot `Application` + `ConversationHandler` (onboarding), `MessageHandler`.
- **Middleware**: message logging (redacted), rate limit.
- **Services**: `dispatch_message`, `handle_voice`, `handle_text`.
- **Rendering**: `templates/bot/*.txt` — response text templates (Uzbek/Russian).

### `apps/rag/`
- **Core pipeline**: `retrieve(query) -> list[Chunk]` → `synthesize(chunks, query) -> Answer`.
- **Embedding**: Gemini text-embedding.
- **Retrieval**: pgvector cosine similarity, filter by language / corpus type.
- **Prompt template**: `system_prompt.md` (citation-forcing, Uzbek register, disclaimer).
- **Confidence score**: response'da `confidence: float` (0-1), threshold logic.
- **Services**: `answer_question(query, user_profile) -> RagAnswer`.
- **No LLM chain frameworks (LangChain, LlamaIndex) — R6**. Direct Gemini SDK call.

### `apps/corpus/`
- **Models**: `Document(source_url, title, version_date, language)`, `Chunk(document_fk, article_ref, content, embedding vector(768))`.
- **Ingestion**: `management/commands/ingest_lex_uz.py`.
- **Diff pipeline**: `services/diff.py` — old_snapshot vs new_snapshot per article.
- **Impact classifier**: `services/impact.py` — LLM prompt: "shu diff shu profile'ga tegishlimi?" → boolean + severity.
- **Cron**: Celery Beat weekly.

### `apps/onboarding/`
- **State machine**: user profile bosqichma-bosqich to'ldiriladi. State field: `EntrepreneurProfile.onboarding_step`.
- **Steps**: `ASK_PROFESSION`, `ASK_REVENUE`, `ASK_EMPLOYEES`, `ASK_FOREIGN`, `ASK_IT_SECTOR`, `ASK_STATUS`, `GENERATE_BRIEFING`.
- **Voice + text**: har step ikkalasini qabul qiladi.
- **Services**: `advance_step`, `parse_answer`, `generate_briefing`.

### `apps/briefing/`
- **Model**: `Briefing(user_fk, generated_at, content_json, pdf_url_optional)`.
- **Composition**: shablon (Jinja2 markdown) + RAG chunks + F3 kalkulyator natijasi + F8 IT Park qarorlari.
- **Output**: markdown (bot) → optional PDF (WeasyPrint yoki gospdf) — Faza 2 uchun.
- **Regeneration**: profile o'zgarsa `regenerate=True`.

### `apps/calculator/`
- **Pure Python** — DB'ga bog'liq emas. Testing oson.
- **Function'lar**: `calc_regime(regime: Regime, revenue: Decimal, params: Params) -> Decimal`.
- **Constants**: 2026 rate'lari `constants.py`'da. Yangi yil — constant yangilanadi + test.
- **Output**: `RegimeSimulation(regime, total_tax, breakdown, sources: list[SourceLink])`.

### `apps/reminders/`
- **Model**: `ScheduledReminder(user_fk, kind, due_date, sent_at, cancelled)`.
- **Kinds**: `QUARTERLY_REPORT, MONTHLY_SOCIAL, ESF, ANNUAL_REPORT, VAT_DECLARATION`.
- **Scheduler**: Celery Beat — daily task "shu kun T-7 / T-3 / T-1 bo'lgan reminderlar" → push.
- **Push channel**: Telegram Bot API sendMessage.
- **User preference**: `Profile.reminder_channels_off: list[str]`.

### `apps/glossary/`
- **Model**: `Term(slug, term_uz_latin, term_uz_cyrillic, term_ru, definition_short, definition_long, sources)`.
- **Seed**: `fixtures/glossary_v1.yaml` (50 term).
- **Auto-link**: RAG response post-processor — matn ichida `Term.term_*` matches → `[atama](https://.../glossary/slug)` link.

### `apps/documents/`
- **Model**: `Template(slug, category, title, description, jinja_content, form_schema_json, sources)`.
- **Rendering**: user javob → Jinja2 render → DOCX (docxtpl) yoki markdown.
- **Categories**: enum (`SHARTNOMA, ARIZA, AKT, HISOB_FAKTURA, BUYRUQ`).

### `apps/checklist/`
- **Model**: `ChecklistItem(slug, regime_scope, question, penalty_amount, source_url)`.
- **Interaction**: bot conversational, har item HA/YO'Q/BILMAYMAN.
- **Scoring**: pure function, oxirida risk score + recommendations.

### `apps/itpark/`
- **Eligibility checker**: pure function, savol → mos/emas.
- **Content**: markdown fayllar `apps/itpark/content/`.

### `apps/voice/`
- **Provider abstraction**:
  ```python
  class VoiceProvider(Protocol):
      async def transcribe(self, audio: bytes, lang: str) -> Transcription: ...
      async def synthesize(self, text: str, lang: str) -> bytes: ...
  ```
- **Concrete**: `GeminiVoiceProvider`.
- **Client**: `httpx.AsyncClient` — lifecycle per-request.
- **Retry**: 3x exponential backoff (0.5s, 1s, 2s).
- **Timeout**: 30s.
- **No disk**: audio in-memory bytes only.

---

## 4. Data model (asosiy entity'lar)

```
User
├── telegram_id (PK, BigInt)
├── username (nullable)
├── language ('uz-Latn' | 'uz-Cyrl' | 'ru')
├── created_at
└── EntrepreneurProfile (OneToOne)
    ├── profession_oked
    ├── expected_annual_revenue (Decimal, UZS)
    ├── employee_count
    ├── has_foreign_clients (bool)
    ├── is_it_sector (bool)
    ├── current_status (enum)
    ├── chosen_regime (enum, nullable)
    ├── onboarding_step (enum)
    └── reminder_channels_off (JSONField list)

Document
├── source_url
├── title
├── version_date
├── language
└── Chunk (1..N)
    ├── article_ref
    ├── content
    └── embedding (vector 768)

Briefing
├── user (FK)
├── generated_at
├── content_json
└── superseded_by (self FK, nullable)

ScheduledReminder
├── user (FK)
├── kind (enum)
├── due_date
├── sent_at (nullable)
└── cancelled (bool)

DiffEvent
├── document (FK)
├── article_ref
├── diff_json (before/after)
├── detected_at
└── UserImpact (M..N through)
    ├── user (FK)
    ├── severity (enum)
    ├── notified_at (nullable)

Template (Document shablon)
ChecklistItem
Term (Glossary)
```

---

## 5. Voice pipeline

```
Telegram voice message
    │
    │  (webhook)
    ▼
bot.handle_voice
    │
    │  audio_bytes = await context.bot.get_file(...).download_as_bytearray()
    ▼
voice.transcribe(audio_bytes, lang='uz-Latn')
    │
    │  Gemini STT (via google-genai)
    ▼
Transcription{text, confidence, detected_lang}
    │
    ▼
bot.route(text)  ──►  RAG.answer(text, user_profile) or wizard step
    │
    ▼
Answer{text_uz, citations, confidence, disclaimer}
    │
    │  [if user has /voice_on]
    ▼
voice.synthesize(text_uz, lang) ──► audio_bytes
    │
    ▼
bot.send_voice(audio_bytes) + send_message(text_uz + citations)
```

**Kritik**:
- Audio bytes local variable'da, function scope tugasa GC.
- Logger'da audio yo'q, matn hash bilan (birinchi 40 char).
- Retry: transient error (5xx, timeout) — 3x. Content error (400) — retry yo'q.

---

## 6. RAG pipeline

```
Query "Yillik 300M sotsam qaysi rejim yaxshiroq?"
    │
    ▼
Query embed (Gemini text-embedding-004)
    │
    ▼
pgvector similarity (cosine, top_k=8)
    │
    │  Filter: language matches, document type in scope
    ▼
Chunks [ArticleRef, Content, SourceURL, Score]
    │
    ▼
Rerank (LLM cross-encoder mini-prompt) — top_k=5
    │
    ▼
Prompt composition:
    - System prompt (citation majburiy, ban list, disclaimer)
    - User query
    - Chunks with source_url refs
    - User profile summary (regime hint, revenue tier)
    ▼
Gemini 2.0 flash → response
    │
    ▼
Parse response:
    - answer_text
    - citations: [{article_ref, source_url}]
    - confidence: float (LLM self-report + heuristic)
    ▼
Post-process:
    - Glossary auto-link (§apps/glossary)
    - Disclaimer footer
    - Ban list check (if "tavsiya qilaman" in text → replace)
    ▼
RagAnswer to bot
```

**Kritik**:
- Citation missing → `LowConfidenceError` → fallback message: "Aniq javob berolmayman. Sertifikatli maslahatchi tavsiya etiladi."
- Prompt versionlanadi (`apps/rag/prompts/v1_synthesis.md`), o'zgarish PR bilan.
- Cache: same query + same profile → response cache 1 soat (Redis).

---

## 7. Corpus ingestion pipeline

```
Celery Beat (haftalik, dushanba 03:00 Asia/Tashkent)
    │
    ▼
task: sync_lex_uz_tax_code
    │
    ▼
For each article ref in Tax Code index:
    ├─ fetch lex.uz?ONDATE=<today>
    ├─ compare with stored latest snapshot
    ├─ if different:
    │   ├─ create DiffEvent
    │   ├─ update Chunk content
    │   ├─ re-embed and update vector
    │   └─ enqueue impact classification
    └─ log ingestion status
    ▼
task: classify_impact(diff_event)
    │
    ▼
For each user profile:
    ├─ LLM prompt: "shu diff shu profile'ga tegishlimi?"
    ├─ severity: HIGH / MEDIUM / LOW / NONE
    └─ create UserImpact if != NONE
    ▼
task: send_diff_notifications
    │
    ▼
For each UserImpact where notified_at is NULL and severity in (HIGH, MEDIUM):
    ├─ compose push (LLM: qisqa xulosa + article link)
    ├─ send Telegram push
    ├─ mark notified_at
    └─ respect per-user weekly cap (≤ 3)
```

**Xatolik holatlari**:
- lex.uz down → oxirgi snapshot ishlaydi, admin log.
- Gemini down → impact classification qayta try (Celery retry).
- Ingestion transactional per article ref.

---

## 8. Deployment topology

### Local dev

```
docker-compose.yml:
- postgres:16 (pgvector image)
- redis:7
- app (Django + uvicorn)
- celery-worker
- celery-beat
```

`.env.example` — barcha kerakli env variable'lar (SECRET_KEY, TELEGRAM_BOT_TOKEN, GEMINI_API_KEY, DATABASE_URL, REDIS_URL, ...).

### Production (Faza 3)

```
VPS (Hetzner CX22, ~$5/oy):
├── Caddy (TLS, reverse proxy)
├── Docker Compose:
│   ├── app (uvicorn workers)
│   ├── celery-worker
│   ├── celery-beat
│   └── redis
└── logs → /var/log (structured JSON)

External:
├── Managed Postgres 16 (Neon, ~$20/oy) — pgvector supported
├── Telegram Bot API webhook
└── Gemini API
```

- **Deploy**: GitHub Actions → SSH → `docker compose pull && up -d` → healthcheck.
- **Rollback**: `docker compose` down + previous image.
- **Migrations**: `python manage.py migrate` in release script; zero-downtime for schema changes (see R8).

### CI (GitHub Actions)

```
.github/workflows/ci.yml:
- lint: ruff check + ruff format --check + djlint --check
- test: pytest --cov (require ≥ 80%)
- build: docker image (main branch)
- deploy: main branch only, SSH deploy
```

---

## 9. Security & Privacy

- **Telegram webhook URL** — secret token: `https://taa.example.com/bot/webhook/<TELEGRAM_WEBHOOK_SECRET>/`.
- **CSP** strict (`default-src 'self'` + Telegram domains).
- **Rate limiting**: bot handler-level, per user_id (django-ratelimit or in-memory Redis).
  - Q&A: 30/min free, unlimited Pro.
  - Voice: 10/min.
- **PII**:
  - `telegram_id` — hashed in logs (SHA-256).
  - INN/JSHSHIR — v1'da saqlamaymiz (F9 lookup — cache 1 soat, keyin drop).
  - Briefing content — Postgres'da encrypted-at-rest (managed provider ensures).
- **Admin disabled in prod** — allow-listed IP only (`INTERNAL_IPS` gated).
- **Secrets**: never in git; GitHub Secrets → deploy.

---

## 10. Observability

### Faza 1 (minimal)

- **Logs**: structured JSON, stdout → captured by docker.
- **Log fields**: `ts, level, event, user_id_hash, request_id, latency_ms`.
- **No PII in logs**.

### Faza 3 (production)

- **Sentry** — error tracking.
- **Uptime**: simple ping (uptimerobot).
- **Optional (v2)**: Grafana/Prometheus, per-pipeline latency.

---

## 11. Performance targets

| Pipeline | p50 | p95 | p99 |
|---|---|---|---|
| RAG Q&A | 2s | 6s | 10s |
| Voice transcribe | 1.5s | 4s | 8s |
| Voice synthesize | 1s | 3s | 6s |
| Utility (INN, MXIK) | 200ms | 800ms | 2s |
| Briefing generation | 4s | 12s | 20s |
| Reminder push | 100ms | 500ms | 1s |

---

## 12. Deferred (v2+)

- Vertex AI fallback (Gemini free tier chegara yaqinlashsa).
- Vector store migration: pgvector → Qdrant (agar kerak bo'lsa, HAJM ≥ 5M chunk).
- CDN (static assets, WebApp'dan keyin).
- Multi-region deploy (hozircha shart emas).
- Full mobile native (kelajakda).

---

## 13. Diagram legend

- **App boundary** — Python module + models + services + tests.
- **Cron task** — Celery Beat scheduled.
- **Sync/async** — voice/RAG async, boshqa sync.
- **External** — dashqi API'lar.

---

Any architectural change requires:
1. This file update.
2. `docs/project-context.md` R4 check.
3. Eric approval.
