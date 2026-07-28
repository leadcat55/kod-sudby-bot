from aiogram import Router, F
from aiogram.types import CallbackQuery, PreCheckoutQuery, LabeledPrice, Message, FSInputFile
from datetime import date
from ..services.database import db
from ..services.payments import payments
from ..services.llm import llm
from ..services.pdf_report import pdf_generator
from ..models.user import User
from ..keyboards.inline import deep_analysis_keyboard, back_to_menu_keyboard
from ..utils.texts import PREMIUM_MENU

router = Router()

PRODUCTS = {
    "buy_basic": {"name": "Базовый отчёт", "price": 199, "stars": 199},
    "buy_full": {"name": "Полный отчёт + совместимость", "price": 499, "stars": 499},
    "buy_subscription": {"name": "Годовая подписка", "price": 2999, "stars": 2999},
}

@router.callback_query(F.data == "premium")
async def show_premium_menu(callback: CallbackQuery):
    """Show deep analysis submenu with three buttons: Матрица судьбы, Квадрат Пифагора, Назад"""
    user = await db.get_user(callback.from_user.id)

    if not user or not user.birth_date:
        await callback.message.edit_text(
            "⚠️ Сначала настройте профиль и укажите дату рождения.",
            reply_markup=back_to_menu_keyboard()
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "🔮 **Глубокий анализ**\n\nВыберите раздел:",
        reply_markup=deep_analysis_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "deep_matrix")
async def handle_deep_matrix(callback: CallbackQuery):
    """Show Fate Matrix (Матрица судьбы) report"""
    user = await db.get_user(callback.from_user.id)

    if not user or not user.birth_date:
        await callback.message.edit_text(
            "⚠️ Сначала настройте профиль.",
            reply_markup=back_to_menu_keyboard()
        )
        await callback.answer()
        return

    birth_date = date.fromisoformat(user.birth_date) if isinstance(user.birth_date, str) else user.birth_date
    result = llm.fate_matrix_text(birth_date, user.full_name)

    await callback.message.edit_text(result, reply_markup=deep_analysis_keyboard(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "deep_pythagorean")
async def handle_deep_pythagorean(callback: CallbackQuery):
    """Show Pythagorean Square (Квадрат Пифагора) report"""
    user = await db.get_user(callback.from_user.id)

    if not user or not user.birth_date:
        await callback.message.edit_text(
            "⚠️ Сначала настройте профиль.",
            reply_markup=back_to_menu_keyboard()
        )
        await callback.answer()
        return

    birth_date = date.fromisoformat(user.birth_date) if isinstance(user.birth_date, str) else user.birth_date
    result = llm.pythagorean_square_text(birth_date, user.full_name)

    await callback.message.edit_text(result, reply_markup=deep_analysis_keyboard(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("buy_"))
async def handle_purchase(callback: CallbackQuery):
    product_key = callback.data
    product = PRODUCTS.get(product_key)
    
    if not product:
        await callback.answer("Ошибка продукта")
        return
    
    # Send invoice
    await callback.message.answer_invoice(
        title=product["name"],
        description=f"Получите {product['name']} для КОД СУДЬБЫ",
        payload=product_key,
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label=product["name"], amount=product["stars"])],
        start_parameter=f"buy_{product_key}"
    )
    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payment = message.successful_payment
    product_key = payment.invoice_payload
    user_id = message.from_user.id
    
    # Update user subscription
    user = await db.get_user(user_id)
    if user:
        from datetime import datetime, timedelta
        if product_key == "buy_subscription":
            user.subscription_status = "premium"
            user.subscription_expires = datetime.now() + timedelta(days=365)
        elif product_key in ("buy_basic", "buy_full"):
            user.premium_reports_count += 1
        await db.update_user(user)
    
    # Send confirmation
    await message.answer(
        f"✅ Оплата прошла успешно!\n\n"
        f"📦 Продукт: {PRODUCTS[product_key]['name']}\n"
        f"💰 Сумма: {payment.total_amount} {payment.currency}\n\n"
        f"⏳ Генерирую ваш отчёт с ИИ-анализом...",
        reply_markup=back_to_menu_keyboard()
    )

    # Generate AI deep analysis and PDF
    if user and user.birth_date and user.full_name:
        try:
            import os

            birth_date = date.fromisoformat(user.birth_date) if isinstance(user.birth_date, str) else user.birth_date

            # Generate AI deep analysis
            ai_analysis = await llm.generate_deep_analysis(birth_date, user.full_name)
            if not ai_analysis:
                ai_analysis = llm._get_fallback_analysis(birth_date, user.full_name)

            # Show AI analysis to user
            await message.answer(f"🤖 ИИ-анализ:\n\n{ai_analysis[:2000]}", parse_mode="Markdown")

            # Generate PDF with AI analysis
            os.makedirs("data/reports", exist_ok=True)
            output_path = f"data/reports/tg_{user_id}_report.pdf"

            pdf_user = User(user_id=user_id, birth_date=user.birth_date, full_name=user.full_name)
            pdf_generator.generate_deep_report(pdf_user, ai_analysis, output_path)

            # Send PDF
            await message.answer_document(FSInputFile(output_path, filename="numerology_report.pdf"))

            os.remove(output_path)
        except Exception as e:
            await message.answer(f"😔 Ошибка генерации отчёта: {e}")
