"""Hand-written seed corpus for local dev.

Five short Uzbek entries covering the tax questions a brand-new
entrepreneur asks first: samozanyatos, YTT 4%, MChJ simplified, IT Park
residency, and deadline calendar. This exists so the DB schema can be
exercised end-to-end without hitting lex.uz — real ingestion lands in
a later story (E02-S02 lex.uz scraper).

Each entry is a plain dict so the seed management command can iterate
without pulling in django-loaddata (which has no VectorField support).
Content is intentionally short (200-500 chars) to keep the local dev
seed fast to embed.
"""

from __future__ import annotations

SEED_ENTRIES: list[dict[str, str]] = [
    {
        "source_url": "seed://tax-basics/samozanyatos",
        "title": "Samozanyatos rejim asoslari",
        "language": "uz-Latn",
        "article_ref": "1",
        "content": (
            "Samozanyatos — jismoniy shaxs sifatida ro‘yxatdan o‘tgan tadbirkorlar uchun "
            "soddalashtirilgan rejim. Aylanma solig‘i stavkasi 4% ni tashkil qiladi. Yillik daromad "
            "chegarasi 100 mln so‘m. Chegara oshsa YTT yoki MChJ rejimiga o‘tish talab qilinadi. "
            "Xodim yollash taqiqlangan, faoliyat ro‘yxati cheklangan. Ro‘yxatdan o‘tish "
            "soliq.uz portali orqali onlayn amalga oshiriladi."
        ),
    },
    {
        "source_url": "seed://tax-basics/ytt-4",
        "title": "YTT 4% aylanma solig‘i",
        "language": "uz-Latn",
        "article_ref": "2",
        "content": (
            "Yakka tartibdagi tadbirkor (YTT) 4% aylanma solig‘i — eng ommabop rejim. Yillik "
            "daromad chegarasi 1 mlrd so‘m. Ba’zi faoliyat turlari uchun taqiqlangan: qimor, "
            "alkogol, aksiz mahsulotlari. Chorak hisoboti majburiy. Xodim yollash mumkin, lekin ish haqi "
            "solig‘i alohida to‘lanadi. MChJ ga o‘tish — chegara yaqinlashsa yoki "
            "investor kirsa."
        ),
    },
    {
        "source_url": "seed://tax-basics/mchj-simplified",
        "title": "MChJ soddalashtirilgan rejim",
        "language": "uz-Latn",
        "article_ref": "3",
        "content": (
            "MChJ (mas’uliyati cheklangan jamiyat) soddalashtirilgan rejim — yuridik shaxs uchun. "
            "Daromad solig‘i 4% aylanmadan. Chegara 10 mlrd so‘m yillik. Buxgalteriya hisoboti "
            "majburiy, lekin umumiy rejimdan sodda. Xodim yollash cheklovsiz. QQS to‘lovchisi "
            "bo‘lish ixtiyoriy — eksport qiluvchilar uchun foydali. Ta’sischi va direktor "
            "bir shaxs bo‘lishi mumkin."
        ),
    },
    {
        "source_url": "seed://tax-basics/it-park",
        "title": "IT Park rezidentligi imtiyozlari",
        "language": "uz-Latn",
        "article_ref": "4",
        "content": (
            "IT Park rezidenti bo‘lish — IT sohasidagi kompaniyalar uchun eng foydali variant. "
            "Foyda solig‘i 0%, QQS 0%, ish haqi solig‘i 7.5% (umumiy 12% o‘rniga). Talablar: "
            "IT faoliyat kodi asosiy, daromadning 90% dan ko‘pi IT xizmatlaridan. Chegaralar: "
            "rezidentlik yillik yangilanadi, shartnomalar IT Park orqali ro‘yxatga olinadi. Ariza "
            "it-park.uz portali orqali topshiriladi."
        ),
    },
    {
        "source_url": "seed://tax-basics/deadlines",
        "title": "Soliq hisobotlari muhlati",
        "language": "uz-Latn",
        "article_ref": "5",
        "content": (
            "Chorak hisoboti (YTT, MChJ soddalashtirilgan) — chorak tugagach 25-sanasigacha "
            "topshiriladi: 25-aprel, 25-iyul, 25-oktyabr, 25-yanvar. Yillik hisobot — 15-fevralgacha "
            "o‘tgan yil uchun. Ish haqi solig‘i va sotsial to‘lovlar — har oy "
            "15-sanasigacha. QQS to‘lovchilar uchun oylik hisobot 25-sanaga. Muhlat "
            "o‘tkazib yuborilsa 500K-2M so‘m jarima. Elektron topshirish — soliq.uz "
            "portali orqali."
        ),
    },
]
