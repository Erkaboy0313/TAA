# TAA — Epics & Stories (Faza 1)

**Version**: 0.1
**Date**: 2026-07-02
**Owner**: Eric
**PM**: John
**Status**: Ready for execution

> Har story = alohida branch = alohida PR (project-context.md R12). Har epic tugagach — deploy-ready holat auditsiya. Faza 1 exit gate: barcha 15 epic tugallanadi + PRD Faza 1 exit gate barcha bandlari yashil.

---

## Umumiy tartib va bog'liqliklar

```
E00 Scaffold ──► E01 Accounts ──►┬─► E02 Corpus ──► E03 RAG ─────┐
                                 │                                │
                                 ├─► E05 Bot Foundation ──────────┼─► E08 Onboarding ─► E09 Briefing
                                 │                                │
                                 └─► E04 Voice ───────────────────┘

                            (parallel content epics — independent):
                            E06 Calculator, E07 Glossary, E11 IT Park

                            (later, after core stable):
                            E10 Reminders, E12 Documents, E13 Checklist,
                            E14 INN/MXIK, E15 Diff Feed
```

**Tavsiya etilgan tartib** (solo dev): E00 → E01 → E05 → E04 → E02 → E03 → E06 + E07 + E11 (parallel) → E08 → E09 → E10 → E14 → E13 → E12 → E15.

---

## Branch naming (R12)

Format: `<type>/<epic-id>-<story-id>-<slug>`

- `feat/E03-S04-rag-synthesis-service`
- `chore/E00-S02-docker-compose-postgres`
- `fix/E05-S03-webhook-signature`
- `docs/E00-S00-readme-badges`

---

## Epic 00 — Foundation & Scaffold

**Goal**: Loyihaning ishga tushiriladigan skeleti — Django, Docker, CI, lint, test infra.
**Feature refs**: — (foundational)
**Assignee**: DevOps agent (Winston)
**Exit criteria**: `make dev` lokal ishlaydi, `make test` ishlaydi, CI yashil.

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E00-S01 | Django project scaffold (`taa/` + minimal `apps/core`) | `chore/E00-S01-django-scaffold` | `python manage.py check` ishlaydi |
| E00-S02 | Docker + docker-compose (postgres+pgvector, redis, app, celery) | `chore/E00-S02-docker-compose` | `docker compose up` ishlaydi, pgvector connect qiladi |
| E00-S03 | `pyproject.toml` + ruff config + pytest config | `chore/E00-S03-pyproject-lint-test` | `ruff check` + `pytest` ishlaydi |
| E00-S04 | Pre-commit hooks + `.gitignore` + `.env.example` | `chore/E00-S04-precommit-gitignore` | `pre-commit run --all-files` yashil |
| E00-S05 | GitHub Actions CI (lint + test on PR) | `ci/E00-S05-github-actions` | PR'da CI check yashil |
| E00-S06 | Single `taa/settings.py` env-driven (decouple) | `chore/E00-S06-single-settings-envconfig` | `.env` variables loading, DEBUG toggle |
| E00-S07 | Base models (`TimestampedModel`) + core exceptions | `feat/E00-S07-core-base-models` | `apps/core/models.py` + `apps/core/exceptions.py` |
| E00-S08 | Makefile / tasks.py (dev, test, migrate, lint, fmt) | `chore/E00-S08-makefile` | `make dev`, `make test` ishlaydi |
| E00-S09 | Django admin skeleton (dev-only, DEBUG gated) | `chore/E00-S09-admin-skeleton` | Admin URL `/admin/` DEBUG=True bo'lsa ishlaydi |

**Epic exit**: DevOps auditsiya → deploy-ready image tayyor, README run instructions bor.

---

## Epic 01 — Accounts (User + Profile)

**Goal**: Telegram identity va tadbirkor profili — barcha keyingi epic'lar uchun foundation.
**Feature refs**: (all — foundational)
**Exit criteria**: User + Profile model migrated, service/selector'lar tests bilan qamrangan.

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E01-S01 | `User` model — telegram_id PK, language | `feat/E01-S01-user-model` | Migration ishlaydi, factory bor |
| E01-S02 | `EntrepreneurProfile` model — 8 field | `feat/E01-S02-profile-model` | 1:1 to User, all fields nullable dastlab |
| E01-S03 | Profile enums (regime, current_status, onboarding_step) | `feat/E01-S03-profile-enums` | `constants.py` + TextChoices |
| E01-S04 | Selector `get_by_telegram_id`, `get_profile` | `feat/E01-S04-account-selectors` | Unit tests |
| E01-S05 | Service `create_user_from_telegram`, `update_profile` | `feat/E01-S05-account-services` | Integration tests real DB |
| E01-S06 | Language detection (uz-Latn / uz-Cyrl / ru) | `feat/E01-S06-language-detection` | Utility function + tests |

---

## Epic 05 — Bot Foundation

**Goal**: Telegram bot skeleton — webhook, dispatcher, /help, /start (empty), middleware.
**Feature refs**: (foundation for F1, F2, F3, F6, F7, F8, F9, F10)
**Exit criteria**: Bot start bilan javob beradi, /help ishlaydi, webhook secure.

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E05-S01 | python-telegram-bot Application + Django integration | `feat/E05-S01-ptb-application-setup` | Bot init, `apps/bot/apps.py` boot |
| E05-S02 | Webhook endpoint (async view, secret validation) | `feat/E05-S02-webhook-endpoint` | Test webhook signature validation |
| E05-S03 | Message dispatcher (text vs voice routing) | `feat/E05-S03-message-dispatcher` | Router unit tests |
| E05-S04 | `/help` handler | `feat/E05-S04-help-handler` | Static help text UZ+RU |
| E05-S05 | `/start` empty handler (E08 to'ldiradi) | `feat/E05-S05-start-handler-stub` | Placeholder response |
| E05-S06 | Logging middleware (PII redacted, hash telegram_id) | `feat/E05-S06-bot-logging-middleware` | Log format tests |
| E05-S07 | Rate limit middleware (per-user token bucket) | `feat/E05-S07-bot-rate-limit` | Test limit enforcement |
| E05-S08 | Response templates infra (`templates/bot/*.txt`) | `feat/E05-S08-bot-template-system` | Jinja2 template rendering |
| E05-S09 | Error handler (user-friendly + logger.exception) | `feat/E05-S09-bot-error-handler` | Error path tests |

---

## Epic 04 — Voice Pipeline

**Goal**: Gemini STT + TTS provider abstraction, retry, timeout, in-memory only.
**Feature refs**: F1 voice input, F2 voice, F3 voice
**Exit criteria**: Voice message → text va text → voice ishlaydi, tests bilan.

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E04-S01 | `VoiceProvider` Protocol + `GeminiVoiceProvider` | `feat/E04-S01-voice-provider-abstraction` | Interface + concrete impl |
| E04-S02 | STT service (`transcribe(audio, lang)`) | `feat/E04-S02-stt-service` | Async, in-memory bytes only |
| E04-S03 | TTS service (`synthesize(text, lang)`) | `feat/E04-S03-tts-service` | Async, audio bytes return |
| E04-S04 | Retry + timeout (3x exp backoff, 30s cap) | `feat/E04-S04-voice-retry-timeout` | Transient vs content error tests |
| E04-S05 | Language detection + normalization (uz-Latn/Cyrl/ru) | `feat/E04-S05-voice-lang-detection` | Auto-detect + user override |
| E04-S06 | Bot integration: voice message → STT → dispatcher | `feat/E04-S06-bot-voice-integration` | E2E flow test |
| E04-S07 | `/voice_on` `/voice_off` user preferences | `feat/E04-S07-voice-preferences` | Profile field + handler |

---

## Epic 02 — Corpus Ingestion

**Goal**: Tax Code + BHMS + clarification xatlari Postgres'ga chunk'langan va embed'langan tarzda saqlash. Haftalik diff pipeline.
**Feature refs**: (foundation for F1, F5)
**Exit criteria**: Full Tax Code corpus indexed, diff pipeline haftalik ishlaydi.

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E02-S01 | `Document` + `Chunk` models (pgvector 768-dim) | `feat/E02-S01-corpus-models` | Migration with vector column |
| E02-S02 | lex.uz HTML scraper (Tax Code) | `feat/E02-S02-lex-uz-scraper` | Stable article ref extraction |
| E02-S03 | Chunker (per article, size ≤ 1500 chars) | `feat/E02-S03-corpus-chunker` | Determimistic chunk boundaries |
| E02-S04 | Embedding service (Gemini text-embedding) | `feat/E02-S04-embedding-service` | Batch API, error handling |
| E02-S05 | Management command `ingest_lex_uz_tax_code` | `feat/E02-S05-management-ingest-cmd` | First full ingest ishlaydi |
| E02-S06 | Celery Beat weekly sync task | `feat/E02-S06-weekly-sync-celery` | Task registered, tick trigger test |
| E02-S07 | Snapshot/diff detection (ONDATE compare) | `feat/E02-S07-snapshot-diff` | Diff detects real article change |
| E02-S08 | `DiffEvent` model + persist | `feat/E02-S08-diff-event-model` | Per-article diff record |
| E02-S09 | BHMS + clarification xatlari secondary corpus | `feat/E02-S09-secondary-corpus` | soliq.uz clarification ingest |
| E02-S10 | Ingestion metrics/log (chunk count, cost) | `feat/E02-S10-ingest-metrics` | Structured log per run |

---

## Epic 03 — RAG Q&A Pipeline (F1)

**Goal**: Sifatli, citation'lı, DUMB-proof soliq Q&A.
**Feature refs**: **F1**
**Exit criteria**: 20 real savoldan 80%+ citation to'g'ri, ban list check clean, latency p95 ≤ 6s.

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E03-S01 | Query embedding + pgvector similarity selector | `feat/E03-S01-vector-search` | Top-K return with score |
| E03-S02 | Rerank stage (LLM cross-encoder mini-prompt) | `feat/E03-S02-rerank-stage` | Score improvement measured |
| E03-S03 | System prompt v1 (`apps/rag/prompts/v1_synthesis.md`) | `feat/E03-S03-system-prompt-v1` | Prompt versioned + tested |
| E03-S04 | RAG synthesis service (Gemini call) | `feat/E03-S04-rag-synthesis` | Async, response parsed |
| E03-S05 | Citation parser + normalizer | `feat/E03-S05-citation-parser` | Extract [Article X] → source URL |
| E03-S06 | Confidence scoring (LLM self-report + heuristic) | `feat/E03-S06-confidence-score` | Threshold logic |
| E03-S07 | Ban list post-processor (R10) | `feat/E03-S07-ban-list-postproc` | Forbidden phrases blocked |
| E03-S08 | Disclaimer footer injector | `feat/E03-S08-disclaimer-footer` | Every response has disclaimer |
| E03-S09 | Response cache (Redis, 1h) | `feat/E03-S09-rag-response-cache` | Cache hit metrics |
| E03-S10 | Bot handler `/ask` + free-form text | `feat/E03-S10-ask-handler` | E2E flow test |
| E03-S11 | Voice input integration (E04-S06) | `feat/E03-S11-voice-rag-integration` | Voice → RAG → text+voice reply |
| E03-S12 | Golden Q&A set + evaluation harness | `test/E03-S12-golden-eval-harness` | 20 Q&A citation check |

---

## Epic 06 — Regime Calculator (F3)

**Goal**: Har soliq rejim uchun yillik hisoblash — pure Python, testda oson, hech "tavsiya qilaman" yo'q.
**Feature refs**: **F3**
**Exit criteria**: Barcha 6 rejim uchun hisoblash to'g'ri, unit test coverage 100%.

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E06-S01 | `Regime` enum + `Params` dataclass | `feat/E06-S01-regime-enum` | TextChoices + constants |
| E06-S02 | Rate constants 2026 (per regime) | `feat/E06-S02-rate-constants-2026` | Documented sources per constant |
| E06-S03 | `calc_regime(regime, revenue, params)` pure function | `feat/E06-S03-calc-regime-pure` | Unit tests all regime |
| E06-S04 | `RegimeSimulation` output structure | `feat/E06-S04-simulation-output` | Dataclass + breakdown |
| E06-S05 | Multi-regime comparison + presenter | `feat/E06-S05-regime-comparison` | Ordered by total_tax |
| E06-S06 | Bot handler `/simulyator` | `feat/E06-S06-simulator-handler` | Interactive form via bot |
| E06-S07 | Threshold warnings (100M, 1B chegara) | `feat/E06-S07-threshold-warnings` | Warning logic tests |

---

## Epic 07 — Glossary (F10)

**Goal**: Plain-Uzbek atama tushuntirish. 50 seed term v1.
**Feature refs**: **F10**
**Exit criteria**: 50 term seed loaded, auto-linker RAG output'ga term'lar joylashtiradi.

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E07-S01 | `Term` model + migration | `feat/E07-S01-term-model` | Full term schema |
| E07-S02 | Fixture `glossary_v1.yaml` (50 term) | `feat/E07-S02-glossary-seed-50` | Loaded via management cmd |
| E07-S03 | Term selector (search, by slug) | `feat/E07-S03-term-selectors` | Aliases + language variants |
| E07-S04 | Auto-linker post-processor | `feat/E07-S04-auto-linker` | Detects terms in text, links |
| E07-S05 | Bot handler `/glossary <atama>` | `feat/E07-S05-glossary-handler` | Direct lookup |
| E07-S06 | Voice: "X deganda nima?" flow | `feat/E07-S06-voice-glossary` | Voice reply integration |

---

## Epic 11 — IT Park Guide (F8)

**Goal**: IT Park rezidentlik eligibility + roadmap.
**Feature refs**: **F8**

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E11-S01 | Eligibility checker pure function | `feat/E11-S01-itpark-eligibility` | 5–8 savol, mos/emas |
| E11-S02 | Content markdown (5–7 qadam) | `feat/E11-S02-itpark-content` | `content/itpark_steps.md` |
| E11-S03 | Tax saving calculator (revenue-based) | `feat/E11-S03-itpark-savings-calc` | Integration with E06 |
| E11-S04 | Bot handler `/it_park` | `feat/E11-S04-itpark-handler` | Interactive |
| E11-S05 | Tests | `test/E11-S05-itpark-tests` | Unit + integration |

---

## Epic 08 — Onboarding Wizard (F2 part 1)

**Goal**: `/start` → conversation → to'liq profil to'ldiriladi.
**Feature refs**: **F2**
**Exit criteria**: Wizard voice/text ikkalasini qabul qiladi, orqaga qaytish, skip ishlaydi.

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E08-S01 | ConversationHandler state machine skeleton | `feat/E08-S01-wizard-state-machine` | State transitions |
| E08-S02 | Step: `ASK_PROFESSION` (OKED lookup hint) | `feat/E08-S02-ask-profession` | Voice + text |
| E08-S03 | Step: `ASK_REVENUE` bashorati | `feat/E08-S03-ask-revenue` | Decimal parse + validation |
| E08-S04 | Step: `ASK_EMPLOYEES` | `feat/E08-S04-ask-employees` | Integer parse |
| E08-S05 | Step: `ASK_FOREIGN_CLIENTS` | `feat/E08-S05-ask-foreign` | Yes/no + follow-up |
| E08-S06 | Step: `ASK_IT_SECTOR` | `feat/E08-S06-ask-it-sector` | Yes/no |
| E08-S07 | Step: `ASK_CURRENT_STATUS` | `feat/E08-S07-ask-status` | firma bor/yo'q |
| E08-S08 | State persistence in `Profile.onboarding_step` | `feat/E08-S08-state-persistence` | Resume after disconnect |
| E08-S09 | `/skip`, `/back`, `/cancel` commands | `feat/E08-S09-wizard-control-cmds` | Navigation |
| E08-S10 | Wizard integration tests | `test/E08-S10-wizard-integration` | Full flow E2E |

---

## Epic 09 — Briefing Generation (F2 part 2)

**Goal**: Personalized briefing chiqarish — 10 bo'lim, citation bilan.
**Feature refs**: **F2**
**Exit criteria**: Alpha user briefing to'liq oldi, "keyingi qadam aniqmi?" ≥4/5.

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E09-S01 | `Briefing` model | `feat/E09-S01-briefing-model` | Content JSONField |
| E09-S02 | Briefing template (Jinja2 markdown) | `feat/E09-S02-briefing-template` | 10 bo'lim skeleton |
| E09-S03 | Composition service (integrate E06, E11, RAG) | `feat/E09-S03-briefing-composition` | End-to-end generation |
| E09-S04 | Section: Profile summary | `feat/E09-S04-section-profile-summary` | User-readable |
| E09-S05 | Section: Regime comparison (from E06) | `feat/E09-S05-section-regime-comparison` | Table format |
| E09-S06 | Section: Tax list + explanations | `feat/E09-S06-section-tax-list` | Per regime taxes |
| E09-S07 | Section: Yearly deadline calendar | `feat/E09-S07-section-calendar` | Per regime |
| E09-S08 | Section: Documents checklist | `feat/E09-S08-section-documents` | Required docs |
| E09-S09 | Section: IT Park view (from E11) | `feat/E09-S09-section-itpark` | If applicable |
| E09-S10 | Section: Common mistakes (from E13 preview) | `feat/E09-S10-section-mistakes` | Regime-specific |
| E09-S11 | Section: Source citations bundle | `feat/E09-S11-section-sources` | All links |
| E09-S12 | Bot delivery + `/briefing` recall | `feat/E09-S12-briefing-delivery-recall` | Handler |
| E09-S13 | Regenerate on profile change | `feat/E09-S13-briefing-regenerate` | Trigger + supersede |
| E09-S14 | Tests + golden briefing | `test/E09-S14-briefing-tests` | Full E2E |

---

## Epic 10 — Deadline Reminders (F4)

**Goal**: Har user rejim'iga mos deadline'lar avtomatik yaratiladi va Telegram push yuboriladi.
**Feature refs**: **F4**

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E10-S01 | `ScheduledReminder` model + kind enum | `feat/E10-S01-reminder-model` | Migration |
| E10-S02 | Reminder template'lar (per kind, UZ+RU) | `feat/E10-S02-reminder-templates` | Text + action buttons |
| E10-S03 | Generation service (from Profile) | `feat/E10-S03-reminder-generation` | Regime → calendar |
| E10-S04 | Celery Beat daily task | `feat/E10-S04-reminder-daily-task` | T-7/T-3/T-1 logic |
| E10-S05 | Push service (Telegram sendMessage) | `feat/E10-S05-push-service` | Delivery + retry |
| E10-S06 | User preferences `/reminders_off` | `feat/E10-S06-reminder-preferences` | Per-kind toggle |
| E10-S07 | Regenerate on regime change | `feat/E10-S07-reminder-regenerate` | Hook to profile update |
| E10-S08 | Tests | `test/E10-S08-reminder-tests` | Time-travel with freezegun |

---

## Epic 14 — INN / MXIK Lookup (F9)

**Goal**: Utility bot commands.
**Feature refs**: **F9**

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E14-S01 | soliq-servis INN API client | `feat/E14-S01-soliq-servis-client` | Partner registration path |
| E14-S02 | MXIK tasnif client | `feat/E14-S02-mxik-client` | Community wrapper approach |
| E14-S03 | Bot handler `/inn <raqam>` | `feat/E14-S03-inn-handler` | Formatted response |
| E14-S04 | Bot handler `/mxik <tavsif>` | `feat/E14-S04-mxik-handler` | Search results |
| E14-S05 | Redis cache 1h | `feat/E14-S05-inn-mxik-cache` | Hit metrics |
| E14-S06 | Voice: "INN 30... tekshir" flow | `feat/E14-S06-voice-inn-lookup` | Integration |
| E14-S07 | Tests | `test/E14-S07-inn-mxik-tests` | Mock external, real cache |

---

## Epic 13 — Fine Prevention Checklist (F6)

**Goal**: Interactive checklist → risk score → tuzatish yo'llari.
**Feature refs**: **F6**

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E13-S01 | `ChecklistItem` model + fixture | `feat/E13-S01-checklist-model` | 15 seed item |
| E13-S02 | Regime-scope filter selector | `feat/E13-S02-checklist-filter` | Per-user filter |
| E13-S03 | Bot conversation `/checklist` | `feat/E13-S03-checklist-conversation` | HA/YO'Q/BILMAYMAN buttons |
| E13-S04 | Risk scoring service | `feat/E13-S04-risk-scoring` | Pure function + tests |
| E13-S05 | Prioritized recommendations output | `feat/E13-S05-checklist-recommendations` | Ordered by penalty |
| E13-S06 | "Eslatib qo'y N kundan keyin" → E10 integration | `feat/E13-S06-checklist-followup-reminder` | Hook |
| E13-S07 | Tests | `test/E13-S07-checklist-tests` | Full E2E |

---

## Epic 12 — Documents Library (F7)

**Goal**: 15 shablon + interactive fill flow + DOCX/markdown output.
**Feature refs**: **F7**

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E12-S01 | `Template` model + form_schema JSON | `feat/E12-S01-template-model` | Migration |
| E12-S02 | 15 shablon content (markdown/Jinja) | `feat/E12-S02-templates-content-15` | Fixture load |
| E12-S03 | Form schema definition per template | `feat/E12-S03-form-schemas` | Field types, validation |
| E12-S04 | Conversational form handler | `feat/E12-S04-form-handler` | Multi-step bot flow |
| E12-S05 | Jinja2 render → markdown output | `feat/E12-S05-markdown-render` | Preview |
| E12-S06 | DOCX rendering (docxtpl) | `feat/E12-S06-docx-render` | Downloadable file |
| E12-S07 | Bot handler `/documents` category menu | `feat/E12-S07-documents-menu` | Categories |
| E12-S08 | Tests | `test/E12-S08-templates-tests` | Full E2E |

---

## Epic 15 — Tax Code Diff Feed (F5)

**Goal**: Yangi Tax Code o'zgarishi → mos user'larga push.
**Feature refs**: **F5**

| Story | Nomi | Branch | Kirish/Chiqish |
|---|---|---|---|
| E15-S01 | `UserImpact` through model | `feat/E15-S01-user-impact-model` | severity enum |
| E15-S02 | Impact classifier LLM prompt | `feat/E15-S02-impact-classifier-prompt` | Versioned |
| E15-S03 | Classify task (per diff × per user) | `feat/E15-S03-classify-task` | Celery batch |
| E15-S04 | Notification composer (LLM summarize) | `feat/E15-S04-notification-composer` | Short push |
| E15-S05 | Push service (rate-limited per user, ≤ 3/week) | `feat/E15-S05-diff-push-service` | Cap enforcement |
| E15-S06 | Bot follow-up "Ta'sir chuqurroq" flow | `feat/E15-S06-diff-followup-flow` | Deep dive |
| E15-S07 | Tests + false-positive baseline | `test/E15-S07-diff-tests` | Metric tracking |

---

## Umumiy metrics

- **Total epics (Faza 1)**: 15
- **Total stories (Faza 1)**: ~110
- **Har story timeline**: 1–4 kun solo dev.
- **Faza 1 taxminiy vaqt**: 10–14 hafta full-time solo.

---

## Approve gate

- [x] PRD tasdiqlandi (2026-07-02)
- [ ] Epics.md tasdiqlandi (Eric)
- [ ] E00 kickoff (DevOps agent)

---

**Har story boshlanishidan oldin**:
1. Branch yaratiladi.
2. Story kodlanadi (project-context R1–R13).
3. Test yoziladi (Tester agent yordamida).
4. Local `pre-commit run --all-files` yashil.
5. PR yaratiladi, DevOps agent audit.
6. Merge (squash) → main.
7. Deploy-ready check → keyingi story.
