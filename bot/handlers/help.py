from aiogram import Router, F
from aiogram.types import CallbackQuery
from ..keyboards.inline import back_to_menu_keyboard

router = Router()

HELP_TEXT = """
❓ **О боте КОД СУДЬБЫ**

🔮 **Что это?**
Бот для нумерологических расчётов и построения Матрицы Судьбы.

📊 **Какие расчёты доступны?**
• Число Жизненного Пути
• Число Души
• Число Личности
• Число Судьбы
• Квадрат Пифагора
• Совместимость

🆓 **Бесплатно:**
• 3 базовых расчёта в месяц
• Краткие описания чисел

💎 **Премиум:**
• Подробные отчёты (PDF)
• Полная Матрица Судьбы
• Совместимость с партнёром
• Персональные прогнозы

⚠️ **Дисклеймер:**
Данный бот носит исключительно развлекательный характер. Все расчёты основаны на нумерологии и не являются научными консультациями.

📩 **Поддержка:** @your_support_username
"""

@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    await callback.message.edit_text(HELP_TEXT, reply_markup=back_to_menu_keyboard(), parse_mode="Markdown")
    await callback.answer()