from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔢 Бесплатные расчёты", callback_data="free_calc")
    )
    builder.row(
        InlineKeyboardButton(text="🔮 Глубокий анализ", callback_data="premium")
    )
    builder.row(
        InlineKeyboardButton(text="👥 Совместимость", callback_data="compatibility"),
        InlineKeyboardButton(text="📊 Матрица судьбы", callback_data="matrix")
    )
    builder.row(
        InlineKeyboardButton(text="🎁 Реферальная программа", callback_data="referrals")
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Профиль", callback_data="profile"),
        InlineKeyboardButton(text="❓ Помощь", callback_data="help")
    )
    return builder.as_markup()

def free_calc_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Число Жизненного Пути", callback_data="calc_life_path")
    )
    builder.row(
        InlineKeyboardButton(text="💫 Число Души", callback_data="calc_soul"),
        InlineKeyboardButton(text="⭐ Число Судьбы", callback_data="calc_destiny")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
    )
    return builder.as_markup()

def premium_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Базовый отчёт — 199 ⭐", callback_data="buy_basic")
    )
    builder.row(
        InlineKeyboardButton(text="💎 Полный отчёт — 499 ⭐", callback_data="buy_full")
    )
    builder.row(
        InlineKeyboardButton(text="👑 Подписка — 2999 ⭐/год", callback_data="buy_subscription")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
    )
    return builder.as_markup()

def deep_analysis_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Матрица судьбы", callback_data="deep_matrix")
    )
    builder.row(
        InlineKeyboardButton(text="🔢 Квадрат Пифагора", callback_data="deep_pythagorean")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
    )
    return builder.as_markup()

def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()

