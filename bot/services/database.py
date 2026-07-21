import aiosqlite
from datetime import date, datetime
from typing import Optional
from ..models.user import User
from ..config import config

class DatabaseService:
    def __init__(self):
        self.db_path = config.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    
    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    birth_date DATE,
                    full_name TEXT,
                    language TEXT DEFAULT 'ru',
                    subscription_status TEXT DEFAULT 'free',
                    subscription_expires TIMESTAMP,
                    referral_code TEXT UNIQUE,
                    invited_by INTEGER,
                    free_calcs_used INTEGER DEFAULT 0,
                    free_calcs_reset_date DATE,
                    premium_reports_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()
    
    async def get_user(self, user_id: int) -> Optional[User]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(
                        user_id=row["user_id"],
                        username=row["username"],
                        first_name=row["first_name"],
                        last_name=row["last_name"],
                        birth_date=row["birth_date"],
                        full_name=row["full_name"],
                        language=row["language"],
                        subscription_status=row["subscription_status"],
                        subscription_expires=row["subscription_expires"],
                        referral_code=row["referral_code"],
                        invited_by=row["invited_by"],
                        free_calcs_used=row["free_calcs_used"],
                        free_calcs_reset_date=row["free_calcs_reset_date"],
                        premium_reports_count=row["premium_reports_count"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"]
                    )
                return None
    
    async def create_user(self, user: User) -> User:
        import uuid
        if not user.referral_code:
            user.referral_code = uuid.uuid4().hex[:8].upper()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, referral_code, invited_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user.user_id, user.username, user.first_name, user.last_name, user.referral_code, user.invited_by))
            await db.commit()
        return user
    
    async def update_user(self, user: User) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET
                    birth_date = ?, full_name = ?, subscription_status = ?,
                    subscription_expires = ?, free_calcs_used = ?,
                    free_calcs_reset_date = ?, premium_reports_count = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (user.birth_date, user.full_name, user.subscription_status,
                  user.subscription_expires, user.free_calcs_used,
                  user.free_calcs_reset_date, user.premium_reports_count, user.user_id))
            await db.commit()
    
    async def increment_free_calcs(self, user_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            today = date.today()
            async with db.execute(
                "SELECT free_calcs_used, free_calcs_reset_date FROM users WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    used, reset_date = row
                    if reset_date != today:
                        used = 0
                    await db.execute(
                        "UPDATE users SET free_calcs_used = ?, free_calcs_reset_date = ? WHERE user_id = ?",
                        (used + 1, today, user_id)
                    )
                    await db.commit()
                    return used + 1
            return 0
    
    async def get_referral_count(self, user_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE invited_by = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

db = DatabaseService()
