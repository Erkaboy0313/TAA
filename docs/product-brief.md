# TAA — Product Brief

**Versiya:** 0.1
**Sana:** 2026-07-02
**PM:** John
**Mahsulot egasi:** Eric
**Status:** approved for PRD

---

## Bir gap

O'zbekiston yangi tadbirkorlari (YTT, MChJ, samozanyatos) uchun **voice-first Telegram AI companion** — soliq, buxgalteriya va yuridik masalalarda "yangi kelgan odam" tilida yo'l ko'rsatadi, kalkulyator va manba bilan.

---

## Muammo

1. **1.21M SME + har yili 80k+ yangi tadbirkor** ochiladi O'zbekistonda. Ularning **50–70% birinchi marta** — buxgalteriya bilim yo'q.
2. **Kod 2020 dan beri deyarli har oy o'zgaradi** — norma.uz / buxgalter.uz paywall'da (yillik 1.7–3.5M so'm).
3. **DavrOn (davlat AI)** hallucinate qiladi va davlat sifatida optimizatsiya taklif qilolmaydi. Buxgalter tilida gapiradi.
4. **Buxgalter ijaraga olish** — oyiga 500k–1.25M so'm eng arzon. Yangi tadbirkor uchun "birinchi kuni" og'irlik.
5. **my.soliq.uz** UX buzuq (DownRadar shikoyatlari doim), yangi user chalkashadi.
6. **6000+ tadbirkor faqat kechikkan hisobot uchun 2.8 mlrd so'm jarima** oldi 9 oyda (2024).

---

## Bo'sh zonalar (raqiblarni yorish uchun)

| Kim | Nima qilmaydi (biz qilamiz) |
|---|---|
| DavrOn (gov AI) | Entrepreneur-first UX, plain Uzbek, proaktiv, optimizatsiya solishtirish |
| Azma Finance | Bepul tier, DUMB UX, Telegram-native, voice |
| Buxgalter.uz | Bepul tier, chat, voice, Telegram push |
| Telegram bot lari | AI reasoning, personalized briefing |
| ChatGPT direct | Citation bilan RAG, o'zbek tili sifat, UZ-specific reliability |

---

## Target user

**v1 alpha (Faza 1, 5–20 kishi, Eric + do'stlar)**:
Eric o'zi — kelajakdagi firma egasi, IT sohasi, YTT/MChJ tanlash bosqichida. Bir necha yaqin dizayner/dev do'st.

**v1 beta (Faza 3, 100+ kishi)**:
O'zbek/rus tilida gaplashuvchi, Telegram'ni kun bo'yi ishlatadigan, 25–40 yosh, birinchi marta firma ochmoqchi yoki 6 oy oldin ochgan tadbirkor. IT, ijodiy sohalar, xizmat ko'rsatish, kichik savdo.

**v2 (Faza 4+)**:
YTT / mikro-MChJ egalari kim mavjud biznesini boshqarayapti, bepul + pulli tier'ga ochiq.

---

## Muvaffaqiyat mezoni

### Faza 1 (Bot MVP — alpha)

- **Onboarding** — 5 kishi to'liq wizard'ni o'tadi va personalized briefing oladi (feedback: "menga foydali edimi?").
- **Q&A aniqligi** — 20 real savoldan 80%+ citation'lar to'g'ri (spot-check).
- **Voice sifati** — o'zbekcha voice input STT ≥85% word accuracy.
- **Response latency** — RAG javob ≤ 6s p95.
- **Deadline reminderlar** — 3 real reminder push qilindi va user ko'rdi.

### Faza 2 (WebApp UI)

- **Retention** — 20 alpha user'dan 60%+ 30-kun ichida qayta kirdi.
- **Task success** — briefing → user aniq keyingi qadamni tushundi (survey: "keyingi qadam aniq bo'ldimi?" ≥4/5).
- **NPS mini** — 20 kishidan NPS ≥ 30.

### Faza 3 (Public beta + monetization ready)

- **100 aktiv user** 30 kun ichida.
- **10 to'lovga tayyor** user (paid tier signal).
- **Konversiya** — bot start → briefing complete ≥ 40%.

---

## 3-fazali reja

### 🚀 Faza 1 — Bot MVP (barcha 10 feature, alpha)

**Nima**: Telegram bot orqali barcha 10 kelishilgan feature ishlaydi. Voice + text. Closed alpha (Eric + 5–20 do'st).

**Nima yo'q**: WebApp UI (Faza 2), monetization (Faza 3), sherik integratsiya (Faza 4).

**Timeline**: ~10–14 hafta solo.

### 🎨 Faza 2 — Telegram WebApp UI

**Nima**: WebApp qatlam. Bot handler'lar WebApp'ga link beradi (jadval, checklist, hujjat preview). Bot chat asosiy qoladi.

**Nima yo'q**: Monetization, public marketing.

**Timeline**: ~6–8 hafta.

### 🌍 Faza 3 — Public Beta + Monetization

**Nima**: Public launch. Pulli obuna (100–300k so'm/oy). Deploy stability, monitoring, Sentry, IT Park MChJ ro'yxati, pd.gov.uz baza ro'yxati.

**Timeline**: ~4–6 hafta.

**Post-launch**: Sherikchilik (PNK sertifikatli tashkilot bilan human review tier), IWALLET cross-link.

---

## Business model

- **Faza 1–2**: bepul (alpha/beta).
- **Faza 3**: freemium.
  - **Bepul tier**: RAG Q&A (kunlik limit), asosiy kalkulyator, deadline reminder.
  - **Pro tier ~150k so'm/oy**: cheklovsiz Q&A, personalized briefing, hujjat shablonlari, diff feed, IT Park guide, voice qatlam.
- **Faza 4**: Human consultant escalation (yig'iladigan komissiya sherikdan).

---

## Constraints

- **Solo dev** (Eric). Timeline haqiqiy — sekinlashish yo'q, lekin feature scope kesilmaydi (Eric qat'iy).
- **Regulatoriy YELLOW** — ЗРУ-787, AI Law, PII. Mahsulot "ma'lumot vositasi" sifatida pozitsiyalanadi (project-context R10).
- **Solo VPS + Managed Postgres** deploy — Hetzner/Neon.
- **Til**: v1 — o'zbek (lotin + kirill) + rus. Ingliz — v2.

---

## Non-goals (v1'da yo'q)

- ❌ Personalized paid optimization/loophole advice (ЗРУ-787).
- ❌ Filing on user's behalf.
- ❌ Sud/advokat integratsiyasi.
- ❌ Multi-tenant B2B (buxgalter tashkilotlari uchun API).
- ❌ Mobile native app.
- ❌ IWALLET direct fork/mixing (bu alohida loyiha).

---

## Suite kelajagi

Bu mahsulot — kelajakdagi "IWALLET Suite / mahsulot oilasi"ning **ikkinchi mahsuloti**. Shared:
- Telegram identity (User model)
- Auth middleware
- Notification infra
- Design tokens (Faza 2+)

Cross-link: har mahsulot Home'da "boshqa mahsulot"ga o'tish tugmasi (Faza 3+).

---

## Approved

Ushbu brief PRD'ga o'tish uchun tayyor. Keyingi hujjat: `docs/prd.md`.
