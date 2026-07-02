# TAA — Product Requirements Document

**Version:** 0.1
**Date:** 2026-07-02
**PM:** John
**Owner:** Eric
**Status:** Draft → Approved

> Bu hujjat mahsulotning **nima**si va **nima uchun**iga to'liq javob beradi. Texnik "qanday" — `docs/architecture.md`. Kod qoidalari — `docs/project-context.md`. Har PR shu hujjatga bog'lanadi.

---

## 1. Vision

**Bir yilda O'zbekiston yangi tadbirkorlarining "birinchi kun" companion'iga aylanish.**

Voice-first, o'zbek/rus tilida, Telegram-native. RAG bilan citation-grounded. DavrOn/Azma/buxgalter.uz'ni entrepreneur-first UX, proaktivlik va bepul asosiy tier bilan yorib o'tadi.

---

## 2. Positioning

**Kim uchun**: birinchi marta firma ochmoqchi bo'lgan o'zbek tadbirkorlari (IT, ijodiy, xizmat, savdo).

**Kimga qarshi**:
- **DavrOn** — davlat AI, buxgalter tilida, hallucinate qiladi, optimizatsiya bermayaydi.
- **Azma Finance** — SaaS, chat emas, pulli, entrepreneur-first UX yo'q.
- **Buxgalter.uz** — expert Q&A paywall'da (~1.7–3.5M so'm/yil).
- **ChatGPT direct** — citation yo'q, UZ-specific reliability past.

**Farqi**:
1. **Plain Uzbek** — "5 yoshli bola" tilida.
2. **Voice-first** — hech kim qilmayapti.
3. **Proaktiv** — deadline push + tax code diff feed + jarima checklist.
4. **Citation** — har javob lex.uz manbasi bilan.
5. **Bepul asosiy tier** + Telegram-native distribution.

---

## 3. Personas

### P1 — Aziza, 27, freelance UX dizayner (primary v1)

- Ishlaydi Bali'dan / Toshkent'dan aralash, oy 25–40M so'm chet el mijozlaridan.
- Firma yo'q, hozircha "hisobsiz" ishlaydi. IT Park eshitgan.
- Telegram'da har kuni. Voice message doim yuboradi.
- "Menga aniq va oddiy aytilsa yaxshi bo'lardi — nima qilish kerakligini".
- **Pain**: chet el mijozlar rasmiy shartnoma so'raydi, valyuta muammosi, soliqdan qo'rqadi.
- **TAA'dan kutgani**: "Voice message qilaman, javob eshitaman, keyingi qadam aniq bo'ladi".

### P2 — Bekzod, 32, kichik studio egasi (v2)

- 6 oy oldin MChJ ochgan, 3 xodim, oyiga 80–150M so'm aylanma.
- Buxgalter oyiga 800k so'mga ijaraga. Har oy shubhalar.
- QQS chegara yaqinlashyapti.
- **Pain**: buxgalterga to'la ishonmayadi, xatolarni tekshirmoqchi.
- **TAA'dan kutgani**: "Buxgalter aytganini tekshiraman, alternativ variantlarni ko'raman".

### P3 — Diyor, 22, tech startup founder (v2)

- Sherikchilikda AI-based startup boshlagan, hali daromad yo'q.
- IT Park rezidentligiga topshirmoqchi.
- **Pain**: hujjat, ariza, huquqiy struktura tanlash.
- **TAA'dan kutgani**: "IT Park bosqichlari, ariza shabloni".

---

## 4. Core Features (10 ta)

Har feature: **F#**, **nomi**, **user story**, **acceptance criteria**, **Phase**, **effort estimate**.

---

### F1 — Tax Code RAG Q&A (citation bilan)

**User story**: Tadbirkor sifatida men Telegram bot'ga soliq / buxgalteriya savolimni yozaman yoki voice message yuboraman, va menga tushunarli javob + manba havolasi keladi.

**AC**:
- ✅ Bot text va audio message qabul qiladi.
- ✅ Audio → STT (Gemini) → tekst savol.
- ✅ RAG retrieval — top 5 tegishli chunk Tax Code / BHMS / clarification'dan.
- ✅ LLM synthesis — javob citation bilan (`[Soliq Kodeksi X-modda](https://lex.uz/...)`).
- ✅ Har javob footer: *"Bu ma'lumot vositasi. Muhim qarorlar uchun sertifikatli maslahatchi kerak."*
- ✅ Confidence past bo'lsa: *"Bu savol bo'yicha aniq javob berolmayman. Sertifikatli maslahatchi tavsiya etiladi."*
- ✅ Voice reply optional: `/voice_on` bilan yoqiladi.
- ✅ Response ≤ 6s p95.
- ✅ Uzbek (Latin + Cyrillic) va Russian ishlaydi.
- ✅ Har javob "🤖 AI" prefix (AI Law compliance).

**Phase**: 1
**Effort**: L (5–7 hafta — RAG pipeline + prompt + evaluation)

---

### F2 — "Yangi tadbirkor" onboarding wizard

**User story**: Bot'ga birinchi kirganimda / `/start` bosganimda, meni voice yoki text bilan intervyu qiladi va menga profilim bo'yicha to'liq personalized briefing (soliq shakli, rejim, deadlines, hujjatlar, IT Park, xatolar) yuboradi.

**AC**:
- ✅ `/start` → conversational wizard boshlaydi.
- ✅ Savol ketma-ketligi: kasb, yillik daromad bashorati, xodim rejasi, chet el mijoz bormi, IT sohasi mi, joriy status (firma bor/yo'q).
- ✅ Har savolga voice yoki text javob mumkin.
- ✅ User `/skip` yoki noaniq javob bersa — reasonable default + flag.
- ✅ Yakunda: PDF/HTML briefing yuboriladi. Briefing tuzilishi:
  1. Sizning profil xulosangiz
  2. Tavsiya etilgan huquqiy shakl(lar) + variantlar solishtirmasi
  3. Har rejim uchun taxminiy yillik soliq (kalkulyator F3 bilan integratsiya)
  4. Sizga taalluqli barcha soliqlar ro'yxati + qisqa tushuntirish
  5. Yillik deadline kalendar
  6. Kerakli hujjatlar ro'yxati
  7. IT Park qarash (F8 bilan integratsiya, mos bo'lsa)
  8. Tipik xatolar (F6 bilan integratsiya)
  9. Har fakt yonida `[manba]` havolasi
  10. Footer disclaimer
- ✅ Briefing saqlanadi, keyin `/briefing` bilan qayta ko'rish mumkin.
- ✅ User ma'lumotlarini o'zgartirsa (`/edit_profile`) — briefing qayta generatsiya.
- ✅ Har qadamda user "orqaga" yoki "tashla" qila oladi.

**Phase**: 1
**Effort**: L (4–5 hafta — wizard state machine + briefing template + LLM composition)

---

### F3 — Soliq rejimi simulyatori (kalkulyator)

**User story**: Men yillik daromadim va xarajatlarim bashoratini kiritaman va har bir soliq rejimida qancha to'lashimni ko'raman.

**AC**:
- ✅ Bot komandasi `/simulyator` yoki wizard ichida.
- ✅ Kirish parametrlari: yillik daromad, xodim soni, o'rtacha xodim maoshi, IT Park rezidentligi (ha/yo'q), valyuta operatsiyalari, faoliyat turi.
- ✅ Chiqish: har rejim (samozanyatos / YTT 4% / YTT 25M / MChJ soddalashtirilgan / MChJ umumiy / IT Park rezident) uchun yillik jami soliq (taxminiy).
- ✅ Har rejim uchun: to'lanishi kerak bo'lgan soliqlar ro'yxati, hisoblash formulasi ko'rinishi ("shaffof").
- ✅ Solishtirish jadvali + eng arzon vs eng qulay ajratib ko'rsatiladi.
- ✅ **Personalized directive YO'Q** — faqat raqamlar (R10). User o'zi tanlaydi.
- ✅ Manba: har hisoblash Tax Code moddasi havolasi bilan.
- ✅ Chegara ogohlantirishlar: "100M chegarasiga yaqin" / "1 mlrd chegarasiga yaqin".

**Phase**: 1
**Effort**: M (2–3 hafta — hisoblash mantiqi + prezentatsiya)

---

### F4 — Deadline reminder tizimi

**User story**: Men soliq rejimimni tanlaganimdan so'ng, bot menga Telegram push orqali har muhim deadline'dan oldin xabar beradi.

**AC**:
- ✅ User profil'ida rejim tanlangandan so'ng — personalized deadline kalendar avtomatik yaratiladi.
- ✅ Reminder turlari (rejimga bog'liq):
  - Chorak hisoboti (25-yanvar, 25-aprel, 25-iyul, 25-oktyabr)
  - Oylik sotsial soliq
  - ESF chastota
  - Yillik hisobot (fevral 15)
  - QQS deklaratsiyasi
- ✅ Push jadvali: **T-7** (haftalik), **T-3** (kuchli), **T-1** (kritik) kunlarda.
- ✅ Har push: "Nima to'lanadi", "Qancha", "Qanday to'lash" tugmalari.
- ✅ User `/reminders_off` bilan o'chira oladi (per-turi ham).
- ✅ Celery Beat scheduler + Redis (background).
- ✅ Rejim o'zgarsa — kalendar avtomatik qayta hisoblanadi.

**Phase**: 1
**Effort**: M (2 hafta — scheduler + push template)

---

### F5 — Tax Code diff feed

**User story**: Yangi Tax Code o'zgarishi bo'lganda va bu mening rejimim / faoliyatimga tegishli bo'lsa, men Telegram push oraqli xabar olaman: nima o'zgardi, sizga qanday ta'sir qiladi, qachondan kuchga kiradi.

**AC**:
- ✅ Haftalik cron: lex.uz Tax Code ONDATE snapshot vs oldingi hafta — diff hisoblash (chunk-level).
- ✅ Har diff chunk → LLM classifier: kimga tegishli (rejim, faoliyat turi, xodim status).
- ✅ Har user profil'iga mos diff filter qilinadi.
- ✅ Mos bo'lsa — Telegram push: "🆕 Sizning [YTT 4% rejim] uchun o'zgarish: [qisqa xulosa]. [To'liq o'qish] [Ta'sir chuqurroq]".
- ✅ "To'liq o'qish" — bot ichida javob bilan qisqacha eski vs yangi solishtirish + manba lex.uz.
- ✅ False-positive < 20% (spot check).
- ✅ Har user haftada ≤ 3 push (spam oldini olish).

**Phase**: 1
**Effort**: M (3 hafta — diff pipeline + impact classifier)

---

### F6 — Jarima oldini olish checklist

**User story**: Men Bot'da checklist'ni ochib, "shu narsalarni qildingizmi?" ro'yxati bo'ylab yuraman va sizga qaysi joyda risk borligi ko'rinadi.

**AC**:
- ✅ Bot komandasi `/checklist`.
- ✅ User rejim'iga mos checklist paydo bo'ladi (5–15 element).
- ✅ Elementlar: "ESF jo'natdingizmi?", "Sotsial soliq 25-da to'landimi?", "Xodim ish shartnomasi rasmiylashtirilganmi?" va h.k.
- ✅ Har element: HA / YO'Q / BILMAYMAN tugmalari.
- ✅ YO'Q yoki BILMAYMAN → nima qilish kerakligi + jarima summasi + manba.
- ✅ Yakunda: risk score + prioritetli tuzatish ro'yxati.
- ✅ User "eslatib qo'y 3 kundan keyin" tanlashi mumkin.

**Phase**: 1
**Effort**: S (1–2 hafta — content + state)

---

### F7 — Hujjat shablonlari kutubxonasi

**User story**: Men Bot'dan asosiy hujjatlar (xizmat shartnomasi, ariza, akt, hisob-faktura shabloni) topa olaman, o'zim to'ldiraman, olib chiqaman.

**AC**:
- ✅ Bot komandasi `/documents` — kategoriya menyu.
- ✅ Kategoriyalar: Shartnomalar, Arizalar, Aktlar, Hisob-fakturalar, Buyruqlar.
- ✅ Har hujjat: kalta tavsif + "namuna" ko'rish + "to'ldirish" tugmalari.
- ✅ "To'ldirish" — bot conversational form (10–15 savol) → tayyor DOCX/PDF.
- ✅ Har shablon huquqiy source bilan (qaysi normativga asoslanadi).
- ✅ v1'da 15 asosiy shablon (Faza 1).
- ✅ Foydalanuvchi tomonidan shablon so'ralganda va yo'q bo'lsa — "so'rov ro'yxati"ga qo'shiladi (feedback loop).

**Phase**: 1
**Effort**: M (2 hafta — 15 shablon markdown + form + DOCX gen)

---

### F8 — IT Park / startup imtiyozlari guide

**User story**: Men IT sohasidamаn (yoki bo'lmoqchiman) va IT Park rezidentligi menga qanchalik mos, foydasi qancha, qanday ariza berish kerakligini bilmoqchiman.

**AC**:
- ✅ Bot komandasi `/it_park`.
- ✅ Eligibility checker: 5–8 savol (faoliyat OKED, sohasi, aylanma, xodim, chet el mijoz).
- ✅ Chiqish: "Sizga mos" / "Ehtimoli bor" / "Hozircha mos emas" + sabab.
- ✅ Mos bo'lsa: soliq imtiyoz taxminiy hisoblash (aylanmangizga asoslangan).
- ✅ Ariza berish yo'l xaritasi: 5–7 qadam, har biriga hujjat ro'yxati.
- ✅ Manba: itpark.uz + Prezident qarorlari havolalari.

**Phase**: 1
**Effort**: S (1 hafta — content + checker + calc)

---

### F9 — INN / MXIK / e-faktura lookup

**User story**: Men Bot'ga INN yoki tashkilot nomi yozaman va tez ma'lumot olaman. Yoki MXIK kod izlab topaman. Yoki mening e-faktura hisobim holatini ko'raman.

**AC**:
- ✅ `/inn <raqam>` — soliq-servis API'dan tashkilot info (nom, manzil, faoliyat OKED, status).
- ✅ `/mxik <tavsif>` — tasnif.soliq.uz API'dan mos MXIK'lar ro'yxati.
- ✅ `/faktura` — user'ning e-faktura holati (partner integration bilan Faza 2/3).
- ✅ Voice bilan ham ishlaydi ("INN 3050... tekshir").
- ✅ Cache 1 soat (INN response).

**Phase**: 1 (partial — INN + MXIK), Faza 2 (e-faktura full)
**Effort**: S (1 hafta — API integratsiya + Telegram formatter)

---

### F10 — Plain Uzbek glossariy / jargon translator

**User story**: Men Bot yozadigan har qanday atama (masalan, "QQS", "aylanma soliq") ustiga bosaman va menga "5 yoshli bola" tilida tushuntirish keladi.

**AC**:
- ✅ Corpus: 150+ asosiy atama v1 uchun.
- ✅ Har atama uchun: 1-jumla tushunarli talqin + kengaytirilgan tushuntirish.
- ✅ Bot mode: `/glossary <atama>` yoki har javobda atamalar `[QQS]`(link) bilan.
- ✅ Automatic detection: bot javob generatsiya qilganda RAG output'ida `constants.GLOSSARY_TERMS` topsa auto-link.
- ✅ Voice: "QQS deganda nima tushuniladi?" — voice reply.
- ✅ UX invariant: har texnik atama iloji boricha oddiy so'zlar bilan almashtiriladi. Almashtirib bo'lmasa — glossariy link.

**Phase**: 1 (baseline 50 atama, kengayadi)
**Effort**: M (2 hafta — content curation + integration)

---

## 5. Feature-to-Phase Matritsa

| # | Feature | Faza 1 (Bot MVP) | Faza 2 (WebApp UI) | Faza 3 (Public beta) |
|---|---|---|---|---|
| F1 | RAG Q&A + voice | ✅ Full | Rich UI cards | Rate limit tier |
| F2 | Onboarding wizard | ✅ Full | Visual wizard flow | Progress save |
| F3 | Regime simulyatori | ✅ Bot response | Interactive table | — |
| F4 | Deadline reminder | ✅ Full | Calendar UI | User preferences |
| F5 | Tax Code diff feed | ✅ Full | Diff preview UI | — |
| F6 | Fine checklist | ✅ Full | Checklist UI + progress | Historical tracking |
| F7 | Hujjat shablonlari | ✅ 15 shablon + DOCX | Preview UI | 30 shablon |
| F8 | IT Park guide | ✅ Full | Visual roadmap | — |
| F9 | INN/MXIK lookup | ✅ INN + MXIK | Full e-faktura | Partner API |
| F10 | Glossariy | ✅ 50 term | Rich tooltip | 150 term |

**Faza 1'da HAR feature ishlaydi** (bot orqali), keyingi fazalar boyitadi va polish qiladi. **Feature drop = KELISHILGAN EMAS**.

---

## 6. 3-Faza gate'lari

### Faza 1 Exit Gate (Bot MVP → Faza 2'ga o'tish uchun)

- [ ] Barcha 10 feature bot'da ishlaydi (AC bo'yicha).
- [ ] Alpha test: 5+ real user briefing'ni to'liq oldi.
- [ ] Q&A citation accuracy ≥ 80% (20 real savol spot-check).
- [ ] Voice STT o'zbek accuracy ≥ 85%.
- [ ] Response latency ≤ 6s p95 (RAG), ≤ 3s p95 (utility).
- [ ] Test coverage: services/selectors ≥ 80%.
- [ ] Har feature uchun kamida 1 E2E flow test.
- [ ] Deploy tayyor (deploy hali qilinmagan, lekin DevOps agent buni tayyorlangan).
- [ ] Regulatory checklist: har javob citation + disclaimer, hech "tavsiya qilaman" yo'q.

### Faza 2 Exit Gate (WebApp UI → Faza 3'ga o'tish uchun)

- [ ] WebApp v1 barcha 10 feature uchun UI qatlami.
- [ ] Mobile-first, Telegram viewport (430px), dark mode.
- [ ] IWALLET brand tokens (shared design system) integratsiya.
- [ ] 20 alpha user'dan 60% 30-kun retention.
- [ ] NPS ≥ 30 (mini-survey).
- [ ] Bot va WebApp arasidagi state sinxron (User model bir).
- [ ] Accessibility (kontrast, touch target ≥ 44px).

### Faza 3 Exit Gate (Public beta ready — deploy)

- [ ] Prod deploy live (Caddy + Docker + Managed Postgres).
- [ ] Monitoring: Sentry (error) + basic uptime.
- [ ] pd.gov.uz'da PII baza ro'yxatga olingan.
- [ ] IT Park rezident MChJ (yoki tayyor plan).
- [ ] Monetization tier ishlaydi (Pro subscription check).
- [ ] 100 aktiv user 30 kun ichida.
- [ ] Support / feedback kanal (Telegram support chat).

**Faza 4+ (kelajakda)**: PNK sertifikatli sherik integratsiya (human review tier), IWALLET Suite cross-link.

---

## 7. Metrics dashboard (v1)

### Product metrics

- Weekly Active Users (WAU)
- Bot start → briefing complete konversiya
- Q&A per user per week
- Voice message share (% of queries)
- Reminder open rate

### Quality metrics

- Citation accuracy (weekly manual spot-check on 20 random Q&A)
- Confidence distribution (histogram)
- STT accuracy (Uzbek Latin, Cyrillic, Russian)
- Latency p50/p95/p99 per pipeline (RAG, voice, utility)
- Response error rate

### Business metrics (Faza 3+)

- Free → Pro conversion
- Churn (monthly)
- Support tickets per user

---

## 8. Constraints

### Solo dev

Eric — bitta developer. Timeline haqiqiy: Faza 1 ~10–14 hafta, Faza 2 ~6–8 hafta, Faza 3 ~4–6 hafta. **Feature drop yo'q**, lekin timeline haqiqiy asoslanadi.

### Regulatory YELLOW (project-context R10)

Har feature ЗРУ-787 (soliq maslahati) + AI Law (human-in-loop) + PII qonuni bilan tekshiriladi. UI tili qat'iy control.

### Tech budget

- Gemini API: ~$20–50/oy Faza 1'da (test/alpha).
- Postgres managed: ~$20/oy.
- VPS: ~$10/oy.
- Domain: ~$15/yil.

### Regional/lingual

- **Uzbek**: Lotin va Kirill ikkalasi. Automatic detection va bir-biriga o'girish.
- **Russian**: to'liq qo'llab-quvvatlash.
- **English**: v2.

---

## 9. Non-goals

- ❌ Personalized paid optimization ("shu rejimni tanlang"). ЗРУ-787.
- ❌ Filing on user's behalf (soliq idorasi bilan direct action).
- ❌ Advokatlik / sud vakili.
- ❌ Multi-tenant B2B API buxgalter tashkilotlari uchun.
- ❌ Mobile native app.
- ❌ IWALLET integratsiya v1'da (suite Faza 3+).
- ❌ Kripto / NFT / xorij faoliyati chuqur qamrovi (RAG qamrasi yetmaydi).
- ❌ Cross-country (Qozog'iston, Rossiya) — faqat UZ.

---

## 10. Dependencies

### External

- **Gemini API** (Google) — LLM + STT + TTS.
- **lex.uz** — Tax Code corpus (scrape).
- **soliq.uz** — clarification xatlari (scrape).
- **api.soliq-servis.uz** — INN lookup (partner registration).
- **tasnif.soliq.uz** — MXIK (community wrapper mavjud).
- **api.faktura.uz** — e-faktura (E-IMZO kerak, Faza 2+).
- **Telegram Bot API** — bot infrastructure.

### Internal

- **project-context.md** — buzilmas qoidalar.
- **architecture.md** — texnik "qanday".
- **DevOps agent** (`.claude/agents/devops.md`) — infrastruktura.
- **Tester agent** (`.claude/agents/tester.md`) — test cases.

---

## 11. Risks

| Risk | Ehtimol | Ta'sir | Mitigation |
|---|---|---|---|
| RAG hallucination → noto'g'ri huquqiy fakt | O | Y | Citation majburiy, confidence threshold, spot-check 20/hafta |
| ЗРУ-787 buzilishi (personalized advice) | O | Y | UI language ban list (R10), review har PR |
| DavrOn tez yaxshilanib qoladi | Y | O | Wedge — entrepreneur UX + voice + proaktivlik |
| Solo dev timeline slip | Y | O | Har hafta hisobot Eric o'ziga, Faza 1'ni sub-milestone bilan |
| Gemini API narx oshishi | P | O | Provider abstraction (D — Dependency Inversion), fallback plan |
| lex.uz layout o'zgarishi | P | O | Scrape monitoring + graceful degradation (oxirgi snapshot) |
| User adoption sekin | O | O | IWALLET cross-link (Faza 3+), YouTube demo, Telegram channel |

Y=Yuqori, O=O'rta, P=Past

---

## 12. Approval

- [x] Product Brief tasdiqlangan (2026-07-02)
- [ ] PRD tasdiqlangan (Eric imzosini kutamiz)
- [ ] Architecture tasdiqlangan
- [ ] Epics/Stories bo'lingan (`docs/epics.md` — Faza 1 uchun keyingi hujjat)

Approved bo'lgach → `bmad-create-epics-and-stories` skill bilan Faza 1 epic'larga bo'linadi.
