import os
from datetime import date, datetime
from typing import Optional, List, Dict, Any

from ..models.user import User
from ..config import config


class DatabaseService:
    def __init__(self):
        self.db_url = config.DATABASE_URL
        self.is_postgres = self.db_url.startswith("postgresql")
        self._pool = None
        print(f"[DB] url starts with: {self.db_url[:20]}... is_postgres={self.is_postgres}")

    async def _get_pool(self):
        if self._pool is None:
            if self.is_postgres:
                import asyncpg
                self._pool = await asyncpg.create_pool(self.db_url, min_size=2, max_size=10)
            else:
                import aiosqlite
                self._pool = await aiosqlite.connect(
                    self.db_url.replace("sqlite+aiosqlite:///", "")
                )
        return self._pool

    async def init_db(self):
        if self.is_postgres:
            await self._init_postgres()
        else:
            await self._init_sqlite()

    async def _init_postgres(self):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    birth_date DATE,
                    full_name TEXT,
                    language TEXT DEFAULT 'ru',
                    subscription_status TEXT DEFAULT 'free',
                    subscription_expires TIMESTAMP,
                    referral_code TEXT UNIQUE,
                    invited_by BIGINT,
                    free_calcs_used INTEGER DEFAULT 0,
                    free_calcs_reset_date DATE,
                    premium_reports_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_payments (
                    payment_id TEXT PRIMARY KEY,
                    user_key TEXT NOT NULL,
                    plan_id TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    async def _init_sqlite(self):
        import aiosqlite
        db = await self._get_pool()
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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pending_payments (
                payment_id TEXT PRIMARY KEY,
                user_key TEXT NOT NULL,
                plan_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

    def _ph(self, n: int) -> str:
        """Return placeholder: ? for sqlite, $1/$2/... for postgres"""
        if self.is_postgres:
            return ", ".join(f"${i}" for i in range(1, n + 1))
        return ", ".join("?" for _ in range(n))

    async def get_user(self, user_id: int) -> Optional[User]:
        if self.is_postgres:
            return await self._get_user_pg(user_id)
        return await self._get_user_sqlite(user_id)

    async def _get_user_pg(self, user_id: int) -> Optional[User]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
            if row:
                return self._row_to_user(row)
            return None

    async def _get_user_sqlite(self, user_id: int) -> Optional[User]:
        import aiosqlite
        db = await self._get_pool()
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_user(row)
            return None

    def _row_to_user(self, row) -> User:
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

    async def create_user(self, user: User) -> User:
        import uuid
        if not user.referral_code:
            user.referral_code = uuid.uuid4().hex[:8].upper()

        if self.is_postgres:
            return await self._create_user_pg(user)
        return await self._create_user_sqlite(user)

    async def _create_user_pg(self, user: User) -> User:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, referral_code, invited_by)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, user.user_id, user.username, user.first_name, user.last_name, user.referral_code, user.invited_by)
        return user

    async def _create_user_sqlite(self, user: User) -> User:
        import aiosqlite
        db = await self._get_pool()
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, referral_code, invited_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user.user_id, user.username, user.first_name, user.last_name, user.referral_code, user.invited_by))
        await db.commit()
        return user

    async def update_user(self, user: User) -> None:
        if self.is_postgres:
            await self._update_user_pg(user)
        else:
            await self._update_user_sqlite(user)

    async def _update_user_pg(self, user: User) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE users SET
                    birth_date = $1, full_name = $2, subscription_status = $3,
                    subscription_expires = $4, free_calcs_used = $5,
                    free_calcs_reset_date = $6, premium_reports_count = $7,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $8
            """, user.birth_date, user.full_name, user.subscription_status,
                user.subscription_expires, user.free_calcs_used,
                user.free_calcs_reset_date, user.premium_reports_count, user.user_id)

    async def _update_user_sqlite(self, user: User) -> None:
        import aiosqlite
        db = await self._get_pool()
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
        if self.is_postgres:
            return await self._increment_free_calcs_pg(user_id)
        return await self._increment_free_calcs_sqlite(user_id)

    async def _increment_free_calcs_pg(self, user_id: int) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT free_calcs_used, free_calcs_reset_date FROM users WHERE user_id = $1",
                user_id
            )
            if row:
                used, reset_date = row["free_calcs_used"], row["free_calcs_reset_date"]
                today = date.today()
                if reset_date != today:
                    used = 0
                await conn.execute(
                    "UPDATE users SET free_calcs_used = $1, free_calcs_reset_date = $2 WHERE user_id = $3",
                    used + 1, today, user_id
                )
                return used + 1
        return 0

    async def _increment_free_calcs_sqlite(self, user_id: int) -> int:
        import aiosqlite
        db = await self._get_pool()
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
        if self.is_postgres:
            return await self._get_referral_count_pg(user_id)
        return await self._get_referral_count_sqlite(user_id)

    async def _get_referral_count_pg(self, user_id: int) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT COUNT(*) as cnt FROM users WHERE invited_by = $1", user_id
            )
            return row["cnt"] if row else 0

    async def _get_referral_count_sqlite(self, user_id: int) -> int:
        import aiosqlite
        db = await self._get_pool()
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE invited_by = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def add_pending_payment(self, payment_id: str, user_key: str, plan_id: str) -> None:
        if self.is_postgres:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO pending_payments (payment_id, user_key, plan_id) VALUES ($1, $2, $3)",
                    payment_id, user_key, plan_id
                )
        else:
            import aiosqlite
            db = await self._get_pool()
            await db.execute(
                "INSERT INTO pending_payments (payment_id, user_key, plan_id) VALUES (?, ?, ?)",
                (payment_id, user_key, plan_id)
            )
            await db.commit()

    async def get_pending_payments(self) -> List[Dict[str, Any]]:
        if self.is_postgres:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM pending_payments WHERE status = 'pending'")
                return [dict(row) for row in rows]
        else:
            import aiosqlite
            db = await self._get_pool()
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM pending_payments WHERE status = 'pending'"
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def update_payment_status(self, payment_id: str, status: str) -> None:
        if self.is_postgres:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE pending_payments SET status = $1, updated_at = CURRENT_TIMESTAMP WHERE payment_id = $2",
                    status, payment_id
                )
        else:
            import aiosqlite
            db = await self._get_pool()
            await db.execute(
                "UPDATE pending_payments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE payment_id = ?",
                (status, payment_id)
            )
            await db.commit()


db = DatabaseService()
