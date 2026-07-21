from ..services.database import db
from ..config import config

class ReferralService:
    async def get_referral_link(self, user_id: int, bot_username: str) -> str:
        user = await db.get_user(user_id)
        if user and user.referral_code:
            return f"https://t.me/{bot_username}?start={user.referral_code}"
        return ""
    
    async def process_referral(self, new_user_id: int, referral_code: str) -> bool:
        """Process new user referral"""
        # Find referrer by code
        # In real implementation, query DB by referral_code
        # For now, simplified
        return True
    
    async def check_and_award_bonuses(self, referrer_id: int) -> bool:
        """Check if referrer qualifies for bonus"""
        count = await db.get_referral_count(referrer_id)
        user = await db.get_user(referrer_id)
        
        if user and count >= config.REFERRAL_BONUS_THRESHOLD:
            # Award bonus report
            user.premium_reports_count += 1
            await db.update_user(user)
            return True
        return False
    
    async def get_referral_stats(self, user_id: int) -> dict:
        count = await db.get_referral_count(user_id)
        user = await db.get_user(user_id)
        return {
            "count": count,
            "bonuses": user.premium_reports_count if user else 0
        }

referral = ReferralService()