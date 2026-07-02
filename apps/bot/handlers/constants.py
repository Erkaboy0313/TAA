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
