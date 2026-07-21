from aiogram import Router, F
from aiogram.types import CallbackQuery

from ..services.database import db
from ..services.referral import referral
from ..keyboards.inline import back_to_menu_keyboard
from ..utils.texts import REFERRAL_MENU

router = Router()

@router.callback_query(F.data == "referrals")
async def show_referral_menu(callback: CallbackQuery):
    bot = callback.bot
    stats = await referral.get_referral_stats(callback.from_user.id)
    link = await referral.get_referral_link(callback.from_user.id, bot.username)
    
    text = REFERRAL_MENU.format(
        bot_username=bot.username,
        referral_code=link.split("start=")[-1] if "start=" in link else "",
        ref_count=stats["count"],
        bonuses=stats["bonuses"]
    )
    
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard(), parse_mode="Markdown")
    await callback.answer()