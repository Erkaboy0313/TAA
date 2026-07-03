"""Inline static bot copy. Promote to templates when a second handler
needs multi-language strings (R2 rule of 3)."""

from apps.accounts.constants import Language

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

HELP_TEXT: dict[str, str] = {
    Language.UZ_LATIN: _HELP_UZ_LATIN,
    Language.UZ_CYRILLIC: _HELP_UZ_CYRILLIC,
    Language.RUSSIAN: _HELP_RUSSIAN,
}

_UNKNOWN_UZ_LATIN = (
    "Bu buyruqni tanimadim. /help ni yuboring — mavjud buyruqlar ro'yxatini beraman."
)
_UNKNOWN_UZ_CYRILLIC = (
    "Бу буйруқни танимадим. /help ни юборинг — мавжуд буйруқлар рўйхатини бераман."
)
_UNKNOWN_RUSSIAN = "Не знаю такую команду. Отправьте /help — покажу доступные команды."

UNKNOWN_COMMAND: dict[str, str] = {
    Language.UZ_LATIN: _UNKNOWN_UZ_LATIN,
    Language.UZ_CYRILLIC: _UNKNOWN_UZ_CYRILLIC,
    Language.RUSSIAN: _UNKNOWN_RUSSIAN,
}

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

START_TEXT: dict[str, str] = {
    Language.UZ_LATIN: _START_UZ_LATIN,
    Language.UZ_CYRILLIC: _START_UZ_CYRILLIC,
    Language.RUSSIAN: _START_RUSSIAN,
}

_RATE_LIMIT_UZ_LATIN = "⏳ Juda ko'p so'rov. Bir daqiqa kuting va qayta urining."
_RATE_LIMIT_UZ_CYRILLIC = "⏳ Жуда кўп сўров. Бир дақиқа кутинг ва қайта уриниб кўринг."
_RATE_LIMIT_RUSSIAN = "⏳ Слишком много запросов. Подождите минуту и попробуйте снова."

RATE_LIMIT_TEXT: dict[str, str] = {
    Language.UZ_LATIN: _RATE_LIMIT_UZ_LATIN,
    Language.UZ_CYRILLIC: _RATE_LIMIT_UZ_CYRILLIC,
    Language.RUSSIAN: _RATE_LIMIT_RUSSIAN,
}
