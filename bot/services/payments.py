import os
import time
import requests
from typing import Optional, Dict, Any

# Plans configuration
PLANS = {
    "basic": {
        "title": "Базовый отчёт — 199 ₽",
        "price": 199,
        "reports": 1,
        "is_sub": False,
    },
    "full": {
        "title": "Полный отчёт — 499 ₽",
        "price": 499,
        "reports": 3,
        "is_sub": False,
    },
    "subscription": {
        "title": "Подписка — 2999 ₽/год",
        "price": 2999,
        "reports": 100,
        "is_sub": True,
        "days": 365,
    },
}

YOOKASSA_SHOP_ID = os.environ.get("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.environ.get("YOOKASSA_SECRET_KEY", "")
YOOKASSA_RETURN_URL = os.environ.get("YOOKASSA_RETURN_URL", "")


class PaymentError(Exception):
    pass


class PaymentService:
    def __init__(self):
        self.base_url = "https://api.yookassa.ru/v3"
        self.session = requests.Session()
        if YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY:
            self.session.auth = (YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)
        self._idempotency_counter = int(time.time() * 1000)

    def is_configured(self) -> bool:
        return bool(YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY)

    def _idempotency_key(self) -> str:
        self._idempotency_counter += 1
        return f"payment_{self._idempotency_counter}"

    def create_payment(self, plan_id: str, user_key: str) -> Dict[str, Any]:
        """Create payment in YooKassa"""
        if not self.is_configured():
            raise PaymentError("ЮKassa не настроена")

        plan = PLANS.get(plan_id)
        if not plan:
            raise PaymentError(f"Неизвестный тариф: {plan_id}")

        try:
            r = self.session.post(
                f"{self.base_url}/payments",
                headers={"Idempotence-Key": self._idempotency_key()},
                json={
                    "amount": {"value": str(plan["price"]), "currency": "RUB"},
                    "confirmation": {"type": "redirect", "return_url": YOOKASSA_RETURN_URL},
                    "capture": True,
                    "description": f"КОД СУДЬБЫ: {plan['title']}",
                    "metadata": {"user_key": user_key, "plan_id": plan_id},
                },
                timeout=30,
            )
            if r.status_code != 200:
                raise PaymentError(f"Ошибка создания платежа: {r.text}")
            data = r.json()

            # Save to pending payments
            import asyncio
            from .database import db
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(db.add_pending_payment(data["id"], user_key, plan_id))
                else:
                    asyncio.run(db.add_pending_payment(data["id"], user_key, plan_id))
            except Exception:
                pass  # Non-critical, payment still created

            return {
                "id": data["id"],
                "confirmation_url": data["confirmation"]["confirmation_url"],
                "status": data["status"],
            }
        except requests.RequestException as e:
            raise PaymentError(f"Сетевая ошибка: {e}")

    def get_status(self, payment_id: str) -> str:
        """Get payment status"""
        if not self.is_configured():
            raise PaymentError("ЮKassa не настроена")
        
        try:
            r = self.session.get(
                f"{self.base_url}/payments/{payment_id}",
                timeout=30,
            )
            if r.status_code != 200:
                raise PaymentError(f"Ошибка проверки статуса: {r.text}")
            return r.json()["status"]
        except requests.RequestException as e:
            raise PaymentError(f"Сетевая ошибка: {e}")


payments = PaymentService()
