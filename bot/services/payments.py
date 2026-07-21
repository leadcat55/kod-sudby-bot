import httpx
from typing import Optional
from ..config import config

class PaymentService:
    def __init__(self):
        self.yookassa_api = "https://api.yookassa.ru/v3"
    
    async def create_payment(
        self, 
        amount: int, 
        description: str, 
        user_id: int,
        return_url: str
    ) -> Optional[str]:
        """Create payment via YooKassa"""
        if not config.YOOKASSA_SHOP_ID:
            # Fallback to Telegram Stars
            return await self.create_telegram_stars_payment(amount, description, user_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.yookassa_api}/payments",
                auth=(config.YOOKASSA_SHOP_ID, config.YOOKASSA_SECRET),
                json={
                    "amount": {"value": str(amount), "currency": "RUB"},
                    "confirmation": {"type": "redirect", "return_url": return_url},
                    "capture": True,
                    "description": description,
                    "metadata": {"user_id": user_id}
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("confirmation", {}).get("confirmation_url")
        return None
    
    async def create_telegram_stars_payment(self, amount: int, description: str, user_id: int) -> Optional[str]:
        """Create Telegram Stars payment (simplified)"""
        # In real implementation, use Telegram's payment API
        # This is a placeholder
        return f"stars_payment_{user_id}_{amount}"

payments = PaymentService()
