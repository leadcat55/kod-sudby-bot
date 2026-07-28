"""Platform-independent dialog logic for КОД СУДЬБЫ.

FSM states:
    START -> ask birth date -> ask name -> show menu
    MENU -> handle menu choices
    CALC -> show calculation results
    PREMIUM -> show premium options
    PAYMENT -> create payment and show link
"""
import threading
from datetime import date
from typing import Optional

from .channels.base import Channel
from .services import db
from .services.numerology import numerology
from .services.llm import llm
from .services.payments import payments, PLANS
from .services.pdf_report import pdf_generator
from .services.referral import referral
from .keyboards.inline import main_menu_keyboard, back_to_menu_keyboard

# States
S_START = "start"
S_WAIT_BIRTHDATE = "wait_birthdate"
S_WAIT_NAME = "wait_name"
S_MENU = "menu"
S_CALC = "calc"
S_PREMIUM = "premium"
S_DEEP_ANALYSIS = "deep_analysis"
S_PAYWALL = "paywall"


# user_key -> state dict
_sessions = {}
_lock = threading.Lock()


def _session(user_key: str) -> dict:
    with _lock:
        return _sessions.setdefault(user_key, {"state": S_START})


def _reset(user_key: str) -> dict:
    with _lock:
        _sessions[user_key] = {"state": S_START}
        return _sessions[user_key]


# Texts
WELCOME = (
    "🔮 Добро пожаловать в КОД СУДЬБЫ!\n\n"
    "Я помогу вам раскрыть тайны вашего числового кода.\n\n"
    "Введите вашу дату рождения (ДД.ММ.ГГГГ):"
)

ASK_NAME = "📝 Теперь введите ваше полное имя (Имя Фамилия):"

MENU_TEXT = "🔮 Выберите раздел:"

CALC_MENU = (
    "🔢 Бесплатные расчёты\n\n"
    "Доступно: {remaining} из {limit}\n\n"
    "Выберите тип расчёта:"
)

PREMIUM_TEXT = (
    "🔮 Глубокий анализ (Премиум)\n\n"
    "Получите детальный отчёт PDF.\n\n"
    "💰 Цены:\n"
    "• Базовый — 199 ₽\n"
    "• Полный — 499 ₽\n"
    "• Подписка — 2999 ₽/год"
)

PAYWALL_TEXT = (
    "💳 Выберите тариф:\n\n"
    "💎 Базовый — 199 ₽ (1 отчёт)\n"
    "🔥 Полный — 499 ₽ (3 отчёта)\n"
    "👑 Подписка — 2999 ₽/год"
)


def _parse_date(text: str) -> Optional[date]:
    """Parse date from DD.MM.YYYY or DD,MM,YYYY format"""
    try:
        normalized = text.strip().replace(",", ".")
        parts = normalized.split(".")
        if len(parts) != 3:
            return None
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        return date(year, month, day)
    except (ValueError, IndexError):
        return None


def handle(user_key: str, channel: Channel) -> None:
    """Handle incoming message from any platform"""
    incoming = channel.incoming
    text = incoming.text.strip()

    sess = _session(user_key)
    state = sess.get("state", S_START)

    # /start always resets
    if text.lower() in ("/start", "start", "начать", "старт"):
        sess = _reset(user_key)
        channel.send_text(WELCOME)
        sess["state"] = S_WAIT_BIRTHDATE
        return

    if state == S_WAIT_BIRTHDATE:
        birth_date = _parse_date(text)
        if not birth_date:
            channel.send_text("❌ Неверный формат. Введите дату как ДД.ММ.ГГГГ:")
            return
        sess["birth_date"] = birth_date.isoformat()
        sess["state"] = S_WAIT_NAME
        channel.send_text(ASK_NAME)
        return

    if state == S_WAIT_NAME:
        sess["full_name"] = text
        # Save to database (sync context — run async in new loop)
        import asyncio
        try:
            asyncio.run(_save_user(user_key, sess))
        except Exception as e:
            pass
        sess["state"] = S_MENU
        channel.send_text(f"✅ Профиль сохранён!\n\n📅 Дата: {sess['birth_date']}\n👤 Имя: {text}")
        _show_menu(channel)
        return

    if state == S_MENU:
        _handle_menu(user_key, text, channel, sess)
        return

    if state == S_CALC:
        _handle_calc(user_key, text, channel, sess)
        return

    if state == S_PREMIUM:
        _handle_premium(user_key, text, channel, sess)
        return

    if state == S_DEEP_ANALYSIS:
        _handle_deep_analysis(user_key, text, channel, sess)
        return

    if state == S_PAYWALL:
        _handle_paywall(user_key, text, channel, sess)
        return

    # Unknown state - reset
    _reset(user_key)
    channel.send_start_keyboard()


def _show_menu(channel: Channel) -> None:
    """Show main menu"""
    options = [
        ("free_calc", "🔢 Бесплатные расчёты"),
        ("new_calc", "🔄 Новый расчёт"),
        ("premium", "🔮 Глубокий анализ"),
        ("referrals", "🎁 Реферальная программа"),
        ("help", "❓ Помощь"),
    ]
    channel.send_buttons(MENU_TEXT, options)


def _handle_menu(user_key: str, text: str, channel: Channel, sess: dict) -> None:
    """Handle menu selection"""
    if text in ("free_calc", "🔢 Бесплатные расчёты"):
        sess["state"] = S_CALC
        _show_calc_menu(channel, user_key)
    elif text in ("new_calc", "🔄 Новый расчёт"):
        sess = _reset(user_key)
        channel.send_text("🔄 Начнём заново!\n\n📅 Введите дату рождения (ДД.ММ.ГГГГ):")
        sess["state"] = S_WAIT_BIRTHDATE
    elif text in ("premium", "🔮 Глубокий анализ"):
        _handle_premium(user_key, text, channel, sess)
    elif text in ("referrals", "🎁 Реферальная программа"):
        _show_referrals(channel, user_key)
    elif text in ("help", "❓ Помощь"):
        _show_help(channel)
    else:
        _show_menu(channel)


def _show_calc_menu(channel: Channel, user_key: str) -> None:
    """Show free calculation menu"""
    options = [
        ("calc:life_path", "📊 Число Жизненного Пути"),
        ("calc:soul", "💫 Число Души"),
        ("calc:destiny", "⭐ Число Судьбы"),
        ("back", "🔙 Назад"),
    ]
    channel.send_buttons("Выберите расчёт:", options)


def _handle_calc(user_key: str, text: str, channel: Channel, sess: dict) -> None:
    """Handle calculation selection"""
    if text in ("back", "🔙 Назад"):
        sess["state"] = S_MENU
        _show_menu(channel)
        return

    calc_type = None
    if text.startswith("calc:") or "Жизненного Пути" in text:
        calc_type = "life_path"
    elif "Души" in text:
        calc_type = "soul"
    elif "Судьбы" in text:
        calc_type = "destiny"

    if calc_type:
        birth_date = date.fromisoformat(sess.get("birth_date", "2000-01-01"))
        full_name = sess.get("full_name", "")

        numbers = numerology.get_basic_numbers(birth_date, full_name)

        if calc_type == "life_path":
            number = numbers["life_path"]
            result = f"🔢 Число Жизненного Пути: {number}\n\n{llm.get_calc_input_description(calc_type)}"
        elif calc_type == "soul":
            number = numbers["soul"]
            result = f"💫 Число Души: {number}\n\n{llm.get_calc_input_description(calc_type)}"
        elif calc_type == "destiny":
            number = numbers["destiny"]
            result = f"⭐ Число Судьбы: {number}\n\n{llm.get_calc_input_description(calc_type)}"
        else:
            result = "Неизвестный тип расчёта"

        channel.send_text(result)

        # AI-расшифровка
        import asyncio
        try:
            interpretation = asyncio.run(
                llm.interpret_number(calc_type, number, birth_date, full_name)
            )
            channel.send_text(interpretation)
        except Exception as e:
            print(f"[LLM] ошибка: {e}", flush=True)

        _show_calc_menu(channel, user_key)


def _handle_premium(user_key: str, text: str, channel: Channel, sess: dict) -> None:
    """Handle deep analysis — show submenu with Матрица судьбы, Квадрат Пифагора, Назад"""
    if text in ("back", "🔙 Назад"):
        sess["state"] = S_MENU
        _show_menu(channel)
        return

    birth_date = date.fromisoformat(sess.get("birth_date", "2000-01-01"))
    full_name = sess.get("full_name", "")

    if not full_name:
        channel.send_text("❌ Сначала пройдите регистрацию (/start)")
        return

    # Show deep analysis submenu
    sess["state"] = S_DEEP_ANALYSIS
    options = [
        ("deep_matrix", "📊 Матрица судьбы"),
        ("deep_pythagorean", "🔢 Квадрат Пифагора"),
        ("back", "🔙 Назад"),
    ]
    channel.send_buttons("🔮 Глубокий анализ\n\nВыберите раздел:", options)


def _handle_deep_analysis(user_key: str, text: str, channel: Channel, sess: dict) -> None:
    """Handle deep analysis submenu selection"""
    if text in ("back", "🔙 Назад"):
        sess["state"] = S_MENU
        _show_menu(channel)
        return

    birth_date = date.fromisoformat(sess.get("birth_date", "2000-01-01"))
    full_name = sess.get("full_name", "")

    if text in ("deep_matrix", "📊 Матрица судьбы"):
        result = llm.fate_matrix_text(birth_date, full_name)
        channel.send_text(result)
    elif text in ("deep_pythagorean", "🔢 Квадрат Пифагора"):
        result = llm.pythagorean_square_text(birth_date, full_name)
        channel.send_text(result)
    else:
        channel.send_text("❌ Неизвестный выбор")

    # Show submenu again
    options = [
        ("deep_matrix", "📊 Матрица судьбы"),
        ("deep_pythagorean", "🔢 Квадрат Пифагора"),
        ("back", "🔙 Назад"),
    ]
    channel.send_buttons("🔮 Глубокий анализ\n\nВыберите раздел:", options)



def _start_payment(user_key: str, plan_id: str, channel: Channel) -> None:
    """Start payment process"""
    if not payments.is_configured():
        channel.send_text("⚠️ Приём оплаты пока не настроен.")
        return

    try:
        pay = payments.create_payment(plan_id, user_key)
        plan = PLANS[plan_id]
        channel.send_text(
            f"💳 Оплата тарифа «{plan['title']}».\n\n"
            f"Перейди по ссылке и оплати:\n{pay['confirmation_url']}\n\n"
            "После оплаты баланс обновится автоматически."
        )
    except Exception as e:
        channel.send_text(f"😔 Ошибка создания платежа: {e}")


def _handle_paywall(user_key: str, text: str, channel: Channel, sess: dict) -> None:
    """Handle paywall selection"""
    pass


def _show_referrals(channel: Channel, user_key: str) -> None:
    """Show referral program"""
    channel.send_text(
        "🎁 Реферальная программа\n\n"
        "Приглашайте друзей и получайте бонусы!\n"
        "За 3 приглашённых — 1 бесплатный отчёт."
    )
    sess = _session(user_key)
    sess["state"] = S_MENU
    _show_menu(channel)


def _show_help(channel: Channel) -> None:
    """Show help text"""
    channel.send_text(
        "❓ О боте КОД СУДЬБЫ\n\n"
        "Бот для нумерологических расчётов.\n\n"
        "Бесплатно: 3 расчёта в месяц\n"
        "Премиум: подробные PDF-отчёты\n\n"
        "⚠️ Данный бот носит развлекательный характер."
    )


async def _save_user(user_key: str, sess: dict) -> None:
    """Save user to database"""
    from .models.user import User

    # Parse user_key to get user_id
    platform, user_id = user_key.split(":")
    user_id = int(user_id)

    user = await db.get_user(user_id)
    if not user:
        user = User(
            user_id=user_id,
            birth_date=sess.get("birth_date"),
            full_name=sess.get("full_name"),
        )
        await db.create_user(user)
    else:
        user.birth_date = sess.get("birth_date")
        user.full_name = sess.get("full_name")
        await db.update_user(user)
