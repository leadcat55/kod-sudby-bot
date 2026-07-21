from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional

@dataclass
class User:
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    full_name: Optional[str] = None
    language: str = "ru"
    subscription_status: str = "free"  # free, basic, premium
    subscription_expires: Optional[datetime] = None
    referral_code: str = ""
    invited_by: Optional[int] = None
    free_calcs_used: int = 0
    free_calcs_reset_date: Optional[date] = None
    premium_reports_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
