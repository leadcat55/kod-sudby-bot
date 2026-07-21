from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from datetime import date
import re

from ..services.database import db
from ..models.user import User
from ..keyboards.inline import main_menu_keyboard
from ..utils.texts import WELCOME_TEXT, PROFILE_SETUP, PROFILE_SAVED

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await db.get_user(message.from_user.id)
    
    if not user:
        # New user - ask for birth date
        await message.answer(WELCOME_TEXT, parse_mode="Markdown")
        # Set state for birth date input
        # We'll use a simple state machine approach
        await db.create_user(User(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        ))
    elif not user.birth_date:
        # User exists but no birth date
        await message.answer(PROFILE_SETUP, parse_mode="Markdown")
    else:
        # Existing user - show menu
        await message.answer(
            f"👋 С возвращением, {user.first_name}!",
            reply_markup=main_menu_keyboard()
        )

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔮 **Главное меню**\n\nВыберите раздел:",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()