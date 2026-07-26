from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from datetime import date

from ..services.database import db
from ..services.numerology import numerology
from ..services.llm import llm
from ..config import config
from ..keyboards.inline import free_calc_keyboard, back_to_menu_keyboard
from ..utils.texts import FREE_CALC_MENU, NO_FREE_CALC

router = Router()

@router.callback_query(F.data == "free_calc")
async def show_free_calc_menu(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)

    if not user or not user.birth_date:
        await callback.message.edit_text(
            "⚠️ Сначала настройте профиль и укажите дату рождения.",
            reply_markup=back_to_menu_keyboard()
        )
        await callback.answer()
        return

    remaining = config.FREE_CALC_LIMIT - user.free_calcs_used
    text = FREE_CALC_MENU.format(remaining=max(0, remaining), limit=config.FREE_CALC_LIMIT)

    await callback.message.edit_text(text, reply_markup=free_calc_keyboard(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("calc_"))
async def handle_calculation(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)

    if not user or not user.birth_date:
        await callback.message.edit_text(
            "⚠️ Сначала настройте профиль.",
            reply_markup=back_to_menu_keyboard()
        )
        await callback.answer()
        return

    # Check free calc limit
    if user.free_calcs_used >= config.FREE_CALC_LIMIT:
        await callback.message.edit_text(NO_FREE_CALC, reply_markup=back_to_menu_keyboard(), parse_mode="Markdown")
        await callback.answer()
        return

    calc_type = callback.data.replace("calc_", "")
    birth_date = date.fromisoformat(user.birth_date) if isinstance(user.birth_date, str) else user.birth_date

    # Calculate
    numbers = numerology.get_basic_numbers(birth_date, user.full_name)

    input_desc = llm.get_calc_input_description(calc_type)

    if calc_type == "life_path":
        result = f"""
🔢 **Число Жизненного Пути: {numbers['life_path']}**

{input_desc}

{get_life_path_description(numbers['life_path'])}
"""
    elif calc_type == "soul":
        result = f"""
💫 **Число Души: {numbers['soul']}**

{input_desc}

{get_soul_description(numbers['soul'])}
"""
    elif calc_type == "destiny":
        result = f"""
⭐ **Число Судьбы: {numbers['destiny']}**

{input_desc}

{get_destiny_description(numbers['destiny'])}
"""
    else:
        result = "Неизвестный тип расчёта"

    # Increment free calcs
    await db.increment_free_calcs(callback.from_user.id)

    await callback.message.edit_text(result, reply_markup=back_to_menu_keyboard(), parse_mode="Markdown")
    await callback.answer()

    # AI interpretation
    try:
        number = numbers[calc_type]
        interpretation = await llm.interpret_number(calc_type, number, birth_date, user.full_name)
        await callback.message.answer(interpretation, parse_mode="Markdown")
    except Exception as e:
        print(f"[LLM] ошибка: {e}", flush=True)

def get_life_path_description(number: int) -> str:
    descriptions = {
        1: "Вы — прирождённый лидер. Ваш путь — создавать и вести за собой.",
        2: "Вы — дипломат и партнёр. Ваш путь — сотрудничество и гармония.",
        3: "Вы — творец и коммуникатор. Ваш путь — самовыражение.",
        4: "Вы — строитель и организатор. Ваш путь — создавать прочные основы.",
        5: "Вы — искатель приключений. Ваш путь — свобода и перемены.",
        6: "Вы — хранитель очага. Ваш путь — забота о близких.",
        7: "Вы — философ и мыслитель. Ваш путь — познание истины.",
        8: "Вы — властитель и материалист. Ваш путь — успех и изобилие.",
        9: "Вы — гуманист и учитель. Ваш путь — служение людям.",
        11: "Мастер-число! Вы — духовный учитель с интуицией.",
        22: "Мастер-число! Вы — великий строитель мирового масштаба.",
        33: "Мастер-число! Вы — учитель любви и сострадания."
    }
    return descriptions.get(number, "Уникальное число с особым значением.")

def get_soul_description(number: int) -> str:
    descriptions = {
        1: "Ваша душа стремится к лидерству и независимости.",
        2: "Ваша душа стремится к партнёрству и гармонии.",
        3: "Ваша душа стремится к творчеству и самовыражению.",
        4: "Ваша душа стремится к стабильности и порядку.",
        5: "Ваша душа стремится к свободе и приключениям.",
        6: "Ваша душа стремится к любви и заботе.",
        7: "Ваша душа стремится к знаниям и мудрости.",
        8: "Ваша душа стремится к успеху и достижениям.",
        9: "Ваша душа стремится к служению и помощи другим."
    }
    return descriptions.get(number, "Ваша душа имеет уникальное предназначение.")

def get_destiny_description(number: int) -> str:
    descriptions = {
        1: "Ваша судьба — стать лидером и первопроходцем.",
        2: "Ваша судьба — создавать мир и гармонию.",
        3: "Ваша судьба — радовать мир творчеством.",
        4: "Ваша судьба — строить прочные основы.",
        5: "Ваша судьба — приносить перемены и свободу.",
        6: "Ваша судьба — дарить любовь и заботу.",
        7: "Ваша судьба — постигать тайны бытия.",
        8: "Ваша судьба — достигать высот успеха.",
        9: "Ваша судьба — служить человечеству."
    }
    return descriptions.get(number, "Ваша судьба уникальна и полна открытий.")
