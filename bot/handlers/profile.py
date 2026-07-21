from aiogram import Router, F
from aiogram.types import CallbackQuery
from ..services.database import db
from ..keyboards.inline import back_to_menu_keyboard

router = Router()

PROFILE_TEXT = """
⚙️ **Ваш профиль**

👤 Имя: {name}
📅 Дата рождения: {birth_date}
📊 Статус: {status}
🔢 Расчётов в этом месяце: {calcs}/{limit}
🎁 Премиум-отчётов: {reports}
"""

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.message.edit_text("⚠️ Профиль не найден", reply_markup=back_to_menu_keyboard())
        await callback.answer()
        return
    
    text = PROFILE_TEXT.format(
        name=user.full_name or "Не указано",
        birth_date=user.birth_date or "Не указана",
        status="💎 Премиум" if user.subscription_status == "premium" else "🆓 Бесплатный",
        calcs=user.free_calcs_used,
        limit=3,
        reports=user.premium_reports_count
    )
    
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(), parse_mode="Markdown")
    await callback.answer()