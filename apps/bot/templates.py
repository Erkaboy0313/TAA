"""Per-language bot response templates.

Three multi-language string dicts (help / start / unknown / rate_limit)
now share a shape, which triggers the R2 rule of 3 — promote them from
inline handler constants into one place with a small render API.

`render_template(name, language, **context)` looks up the bundle, picks
the language (falling back to `uz-Latn`), and runs `str.format(**context)`
if any keyword args are provided. No Jinja2 yet — plain `.format()`
covers every current caller. Add Jinja2 when a template needs a loop
or conditional (R6).
"""

from __future__ import annotations

from apps.accounts.constants import Language

# ------------------------- /help ------------------------- #

_HELP_UZ_LATIN = """
👋 Salom! Men TAA — soliq, buxgalteriya va yuridik masalalar bo'yicha
yordamchi botman.

Nima qila olaman:
• /help — shu yordam matni
• /start — birinchi sozlash (tez orada)
• matn yoki ovoz orqali savol yuboring — javob beraman

Bu ma'lumot vositasi. Muhim qarorlar uchun sertifikatli maslahatchi
kerak bo'ladi.
""".strip()

_HELP_UZ_CYRILLIC = """
👋 Салом! Мен TAA — солиқ, бухгалтерия ва юридик масалалар бўйича
ёрдамчи ботман.

Нима қила оламан:
• /help — шу ёрдам матни
• /start — биринчи созлаш (тез орада)
• матн ёки овоз орқали савол юборинг — жавоб бераман

Бу маълумот воситаси. Муҳим қарорлар учун сертификатли маслаҳатчи
керак бўлади.
""".strip()

_HELP_RUSSIAN = """
👋 Здравствуйте! Я TAA — бот-помощник по вопросам налогов,
бухгалтерии и юридическим вопросам.

Что я умею:
• /help — этот текст помощи
• /start — первичная настройка (скоро)
• отправьте вопрос текстом или голосом — я отвечу

Это информационный сервис. Для важных решений обратитесь к
сертифицированному консультанту.
""".strip()

# ------------------------- /start ------------------------- #

_START_UZ_LATIN = """
👋 Salom! Men TAA — soliq va buxgalteriya bo'yicha yordamchi botman.

Onboarding sehirgari tez orada tayyor bo'ladi — u sizning faoliyatingizni
so'raydi va shaxsiy soliq brifingini beradi.

Hozircha:
• /help — mavjud imkoniyatlar
• matn yoki ovoz orqali savol bering — javob beraman

Bu ma'lumot vositasi. Muhim qarorlar uchun sertifikatli maslahatchi
kerak bo'ladi.
""".strip()

_START_UZ_CYRILLIC = """
👋 Салом! Мен TAA — солиқ ва бухгалтерия бўйича ёрдамчи ботман.

Онбординг сеҳирғари тез орада тайёр бўлади — у сизнинг фаолиятингизни
сўрайди ва шахсий солиқ брифингини беради.

Ҳозирча:
• /help — мавжуд имкониятлар
• матн ёки овоз орқали савол беринг — жавоб бераман

Бу маълумот воситаси. Муҳим қарорлар учун сертификатли маслаҳатчи
керак бўлади.
""".strip()

_START_RUSSIAN = """
👋 Здравствуйте! Я TAA — бот-помощник по налогам и бухгалтерии.

Мастер онбординга скоро будет готов — он расспросит о вашей
деятельности и подготовит персональный налоговый брифинг.

Пока доступно:
• /help — что я умею
• отправьте вопрос текстом или голосом — отвечу

Это информационный сервис. Для важных решений обратитесь к
сертифицированному консультанту.
""".strip()

# ------------------------- Unknown command ------------------------- #

_UNKNOWN_UZ_LATIN = (
    "Bu buyruqni tanimadim. /help ni yuboring — mavjud buyruqlar ro'yxatini beraman."
)
_UNKNOWN_UZ_CYRILLIC = (
    "Бу буйруқни танимадим. /help ни юборинг — мавжуд буйруқлар рўйхатини бераман."
)
_UNKNOWN_RUSSIAN = "Не знаю такую команду. Отправьте /help — покажу доступные команды."

# ------------------------- Rate limit ------------------------- #

_RATE_LIMIT_UZ_LATIN = "⏳ Juda ko'p so'rov. Bir daqiqa kuting va qayta urining."
_RATE_LIMIT_UZ_CYRILLIC = "⏳ Жуда кўп сўров. Бир дақиқа кутинг ва қайта уриниб кўринг."
_RATE_LIMIT_RUSSIAN = "⏳ Слишком много запросов. Подождите минуту и попробуйте снова."

# ------------------------- Unexpected error ------------------------- #

_ERROR_UZ_LATIN = (
    "😔 Kutilmagan xatolik yuz berdi. Biroz kutib qayta urining — muammo tez orada hal bo'ladi."
)
_ERROR_UZ_CYRILLIC = (
    "😔 Кутилмаган хатолик юз берди. Бироз кутиб қайта уриниб кўринг — муаммо тез орада ҳал бўлади."
)
_ERROR_RUSSIAN = (
    "😔 Произошла неожиданная ошибка. Подождите немного и попробуйте снова — мы уже разбираемся."
)

# ------------------------- Voice echo ------------------------- #

_VOICE_ECHO_UZ_LATIN = "🎙 Sizning savolingiz: {transcript}"
_VOICE_ECHO_UZ_CYRILLIC = "🎙 Сизнинг саволингиз: {transcript}"
_VOICE_ECHO_RUSSIAN = "🎙 Ваш вопрос: {transcript}"

# ------------------------- Voice failure ------------------------- #

_VOICE_FAILED_UZ_LATIN = "😔 Ovozni tushuna olmadim. Yana urunib ko'ring."
_VOICE_FAILED_UZ_CYRILLIC = "😔 Овозни тушуна олмадим. Яна уруниб кўринг."
_VOICE_FAILED_RUSSIAN = "😔 Не удалось распознать голос. Попробуйте ещё раз."


TEMPLATES: dict[str, dict[str, str]] = {
    "help": {
        Language.UZ_LATIN: _HELP_UZ_LATIN,
        Language.UZ_CYRILLIC: _HELP_UZ_CYRILLIC,
        Language.RUSSIAN: _HELP_RUSSIAN,
    },
    "start": {
        Language.UZ_LATIN: _START_UZ_LATIN,
        Language.UZ_CYRILLIC: _START_UZ_CYRILLIC,
        Language.RUSSIAN: _START_RUSSIAN,
    },
    "unknown_command": {
        Language.UZ_LATIN: _UNKNOWN_UZ_LATIN,
        Language.UZ_CYRILLIC: _UNKNOWN_UZ_CYRILLIC,
        Language.RUSSIAN: _UNKNOWN_RUSSIAN,
    },
    "rate_limit": {
        Language.UZ_LATIN: _RATE_LIMIT_UZ_LATIN,
        Language.UZ_CYRILLIC: _RATE_LIMIT_UZ_CYRILLIC,
        Language.RUSSIAN: _RATE_LIMIT_RUSSIAN,
    },
    "unexpected_error": {
        Language.UZ_LATIN: _ERROR_UZ_LATIN,
        Language.UZ_CYRILLIC: _ERROR_UZ_CYRILLIC,
        Language.RUSSIAN: _ERROR_RUSSIAN,
    },
    "voice_echo": {
        Language.UZ_LATIN: _VOICE_ECHO_UZ_LATIN,
        Language.UZ_CYRILLIC: _VOICE_ECHO_UZ_CYRILLIC,
        Language.RUSSIAN: _VOICE_ECHO_RUSSIAN,
    },
    "voice_failed": {
        Language.UZ_LATIN: _VOICE_FAILED_UZ_LATIN,
        Language.UZ_CYRILLIC: _VOICE_FAILED_UZ_CYRILLIC,
        Language.RUSSIAN: _VOICE_FAILED_RUSSIAN,
    },
}


def render_template(name: str, language: str, /, **context: str) -> str:
    """Return a rendered bot response.

    `name` and `language` are positional-only so callers can pass
    `name="Aziza"` as a template context variable without colliding with
    the template selector.

    Falls back to Uzbek-Latin if `language` is not in the bundle. If
    `context` is empty the raw string is returned unchanged, avoiding
    accidental `{...}` interpolation on literal braces the copy might
    contain (KeyError on stray placeholders is preferable to silent
    corruption).
    """
    bundle = TEMPLATES[name]
    body = bundle.get(language) or bundle[Language.UZ_LATIN]
    return body.format(**context) if context else body
